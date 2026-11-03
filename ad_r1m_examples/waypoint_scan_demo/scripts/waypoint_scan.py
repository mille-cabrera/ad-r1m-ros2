#! /usr/bin/env python3
"""
Nav2 waypoint + scan demo.

For each waypoint: navigate with Nav2 (NavigateToPose), then perform a scan in place:
rotate left, back to center, rotate right, and back to center, while capturing frames.
Frame capture is a placeholder (see FrameCapture).

Usage:
  ros2 run ad_r1m_examples waypoint_scan.py --config /path/to/waypoints.yaml
  ros2 run ad_r1m_examples waypoint_scan.py --waypoints-file /path/to/saved_wps.yaml
  ros2 run ad_r1m_examples waypoint_scan.py --ros-args -p use_sim_time:=true
"""

import argparse
import math
import os
import sys
import time

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.utilities import remove_ros_args
import yaml


DEFAULT_CONFIG = {
    'frame_id': 'map',
    'localizer': 'amcl',
    'set_initial_pose': False,
    'initial_pose': {'x': 0.0, 'y': 0.0, 'yaw_deg': 0.0},
    'loops': 1,
    'nav_timeout_sec': 120.0,
    'nav_retries': 1,
    'scan': {
        'left_deg': 90.0,
        'right_deg': 90.0,
        'return_to_center': True,
        'dwell_sec': 1.0,
        'spin_time_allowance_sec': 15,
        'capture_rate_hz': 5.0,
    },
    'waypoints': [],
}


class FrameCapture:
    """
    Placeholder for frame capture during the scan.

    Replace the bodies of start(), capture() and stop() with real camera / ToF capture
    (e.g. subscribe to an image topic and save the latest frame with its pose).
    """

    def __init__(self, logger, rate_hz):
        self._logger = logger
        self._period = 1.0 / rate_hz if rate_hz > 0.0 else 0.0
        self._last_capture = 0.0
        self.frame_count = 0

    def start(self, waypoint_name):
        self.frame_count = 0
        self._logger.info(f'[capture] start scan at {waypoint_name}')

    def capture(self, waypoint_name, yaw_offset_rad, force=False):
        """Capture one frame, rate-limited unless force=True. Yaw is relative to scan center."""
        now = time.monotonic()
        if not force and now - self._last_capture < self._period:
            return
        self._last_capture = now
        self.frame_count += 1
        # TODO: grab the latest frame here and store it with waypoint_name / yaw.
        self._logger.info(
            f'[capture] {waypoint_name} frame #{self.frame_count} '
            f'yaw={math.degrees(yaw_offset_rad):+.1f} deg')

    def stop(self, waypoint_name):
        self._logger.info(
            f'[capture] stop scan at {waypoint_name}: {self.frame_count} frames')


def make_pose(navigator, frame_id, x, y, yaw_deg):
    pose = PoseStamped()
    pose.header.frame_id = frame_id
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    yaw = math.radians(float(yaw_deg))
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def load_nav2_panel_waypoints(path):
    """
    Load waypoints saved with the Nav2 RViz panel 'Save WPs' button.

    Format: waypoints: {waypointN: {pose: [x, y, z], orientation: [w, x, y, z]}}
    Returns a list of {name, x, y, yaw_deg} ordered by N.
    """
    with open(path, 'r') as f:
        data = yaml.safe_load(f) or {}
    entries = data.get('waypoints') or {}
    if not isinstance(entries, dict):
        raise ValueError(f'{path}: expected a "waypoints" map (Nav2 panel Save WPs format)')

    def index(key):
        digits = ''.join(c for c in str(key) if c.isdigit())
        return int(digits) if digits else 0

    waypoints = []
    for key in sorted(entries, key=index):
        entry = entries[key]
        x, y = entry['pose'][0], entry['pose'][1]
        qw, qx, qy, qz = entry['orientation']
        yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
        waypoints.append({'name': str(key), 'x': float(x), 'y': float(y),
                          'yaw_deg': math.degrees(yaw)})
    return waypoints


def load_config(path, waypoints_file=None):
    """
    Load the demo config; waypoints come from waypoints_file if given.

    waypoints_file (CLI) overrides the config 'waypoints_file' key, which overrides the
    inline 'waypoints' list. Relative config paths are resolved against the config file.
    """
    config = {**DEFAULT_CONFIG, 'scan': dict(DEFAULT_CONFIG['scan'])}
    with open(path, 'r') as f:
        user = yaml.safe_load(f) or {}
    user = user.get('waypoint_scan', user)
    config['scan'].update(user.pop('scan', None) or {})
    config.update(user)

    if not waypoints_file and config.get('waypoints_file'):
        waypoints_file = os.path.join(
            os.path.dirname(os.path.abspath(path)), os.path.expanduser(config['waypoints_file']))
    if waypoints_file:
        config['waypoints'] = load_nav2_panel_waypoints(waypoints_file)
        source = waypoints_file
    else:
        source = path
    if not config['waypoints']:
        raise ValueError(f'No waypoints defined in {source}')
    return config


def navigate_to(navigator, pose, name, timeout_sec, retries):
    """Drive to pose with NavigateToPose. Returns True on success."""
    for attempt in range(retries + 1):
        if attempt > 0:
            navigator.warn(f'Retrying {name} ({attempt}/{retries}) after clearing costmaps')
            navigator.clearAllCostmaps()

        pose.header.stamp = navigator.get_clock().now().to_msg()
        if not navigator.goToPose(pose):
            continue

        last_log = -2.0
        while not navigator.isTaskComplete():
            feedback = navigator.getFeedback()
            if feedback is None:
                continue
            elapsed = feedback.navigation_time.sec + feedback.navigation_time.nanosec * 1e-9
            if elapsed - last_log >= 2.0:
                last_log = elapsed
                navigator.info(
                    f'-> {name}: {feedback.distance_remaining:.2f} m remaining, '
                    f'{elapsed:.0f} s elapsed, {feedback.number_of_recoveries} recoveries')
            if elapsed > timeout_sec:
                navigator.warn(f'Timeout navigating to {name}, canceling')
                navigator.cancelTask()

        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            return True
        navigator.warn(f'Navigation to {name} ended with {result}')
    return False


def spin_relative(navigator, angle_rad, time_allowance_sec, capture, name, offset_rad):
    """
    Rotate in place by angle_rad (+ = left/CCW, - = right/CW) using the Nav2 Spin behavior.

    Captures frames while rotating. Returns (succeeded, signed angle actually rotated).
    """
    if not navigator.spin(spin_dist=angle_rad, time_allowance=int(math.ceil(time_allowance_sec))):
        return False, 0.0

    rotated = 0.0
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback is not None:
            rotated = feedback.angular_distance_traveled
        capture.capture(name, offset_rad + rotated)

    if navigator.getResult() == TaskResult.SUCCEEDED:
        return True, angle_rad
    return False, rotated


def dwell(seconds, capture, name, offset_rad):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        capture.capture(name, offset_rad)
        time.sleep(0.05)


def scan(navigator, name, scan_cfg, capture):
    """Left -> center -> right (-> center) scan. Returns True if all rotations succeeded."""
    targets = [math.radians(scan_cfg['left_deg']), 0.0, -math.radians(scan_cfg['right_deg'])]
    if scan_cfg['return_to_center']:
        targets.append(0.0)

    offset = 0.0  # current heading relative to the scan center (rad)
    ok = True
    capture.start(name)
    capture.capture(name, offset, force=True)

    for target in targets:
        delta = target - offset
        if abs(delta) < math.radians(1.0):
            continue
        navigator.info(f'Scan {name}: rotating {math.degrees(delta):+.0f} deg')
        succeeded, rotated = spin_relative(
            navigator, delta, scan_cfg['spin_time_allowance_sec'], capture, name, offset)
        offset += rotated
        capture.capture(name, offset, force=True)
        if not succeeded:
            navigator.warn(f'Scan {name}: rotation failed at {math.degrees(offset):+.0f} deg')
            ok = False
            break
        dwell(scan_cfg['dwell_sec'], capture, name, offset)

    # Best effort: face the scan center again so the next goal starts from a known heading.
    if not ok and scan_cfg['return_to_center'] and abs(offset) > math.radians(1.0):
        navigator.info(f'Scan {name}: restoring center heading')
        _, rotated = spin_relative(
            navigator, -offset, scan_cfg['spin_time_allowance_sec'], capture, name, offset)
        offset += rotated

    capture.stop(name)
    return ok


def wait_for_localization(navigator, config):
    """
    Wait for Nav2 without letting BasicNavigator publish a default (0,0) initial pose.

    waitUntilNav2Active() with AMCL publishes navigator.initial_pose (origin by default)
    until amcl_pose is received, so either set the configured pose or wait for AMCL's
    existing (latched) pose first.
    """
    localizer = config['localizer']
    if config['set_initial_pose']:
        p = config['initial_pose']
        navigator.setInitialPose(
            make_pose(navigator, config['frame_id'], p['x'], p['y'], p['yaw_deg']))
    elif localizer == 'amcl':
        navigator.info('Waiting for current amcl_pose (set it with 2D Pose Estimate in RViz)')
        deadline = time.monotonic() + 30.0
        while not navigator.initial_pose_received and time.monotonic() < deadline:
            rclpy.spin_once(navigator, timeout_sec=0.5)
        if not navigator.initial_pose_received:
            navigator.error('No amcl_pose received; set the pose in RViz or set_initial_pose')
            return False
    navigator.waitUntilNav2Active(localizer=localizer)
    return True


def run(navigator, config, capture):
    """Run the waypoint loop. Returns a process exit code."""
    if not wait_for_localization(navigator, config):
        return 1

    exit_code = 0
    waypoints = config['waypoints']
    loops = int(config['loops'])
    loop = 0
    while loops <= 0 or loop < loops:
        loop += 1
        navigator.info(f'=== Loop {loop}{"" if loops <= 0 else f"/{loops}"} ===')
        for i, wp in enumerate(waypoints, 1):
            name = wp.get('name', f'WP{i}')
            navigator.info(f'Waypoint {i}/{len(waypoints)}: {name}')
            pose = make_pose(
                navigator, config['frame_id'], wp['x'], wp['y'], wp.get('yaw_deg', 0.0))
            if not navigate_to(navigator, pose, name,
                               float(config['nav_timeout_sec']), int(config['nav_retries'])):
                navigator.error(f'Skipping scan at {name}: navigation failed')
                exit_code = 1
                continue
            if wp.get('scan', True) and not scan(navigator, name, config['scan'], capture):
                exit_code = 1
    navigator.info('Waypoint scan finished')
    return exit_code


def default_config_path():
    return os.path.join(
        get_package_share_directory('ad_r1m_examples'),
        'waypoint_scan_demo', 'config', 'waypoints.yaml')


def main():
    rclpy.init(args=sys.argv)
    parser = argparse.ArgumentParser(description='Nav2 waypoint + scan demo')
    parser.add_argument('--config', default=None, help='Waypoints YAML file')
    parser.add_argument('--waypoints-file', default='',
                        help='Waypoints saved with the Nav2 RViz panel "Save WPs" button')
    parser.add_argument('--namespace', default='', help='Robot namespace')
    args = parser.parse_args(remove_ros_args(sys.argv)[1:])

    config = load_config(args.config or default_config_path(), args.waypoints_file or None)
    waypoint_names = ', '.join(wp.get('name', '?') for wp in config['waypoints'])
    navigator = BasicNavigator(node_name='waypoint_scan', namespace=args.namespace)
    navigator.info(f'Loaded {len(config["waypoints"])} waypoints: {waypoint_names}')
    capture = FrameCapture(navigator.get_logger(), float(config['scan']['capture_rate_hz']))

    exit_code = 0
    try:
        exit_code = run(navigator, config, capture)
    except KeyboardInterrupt:
        exit_code = 130
        try:
            navigator.cancelTask()
        except Exception:
            pass
    finally:
        navigator.destroyNode()
        if rclpy.ok():
            rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
