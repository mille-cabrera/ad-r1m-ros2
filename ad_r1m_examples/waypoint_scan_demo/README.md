# Waypoint Scan Demo

Drive the AD-R1M through a list of Nav2 waypoints and, at each one, scan in place
while capturing frames:

```
go to waypoint -> left 90 deg -> center -> right 90 deg -> center -> next waypoint
```

Built on [`nav2_simple_commander`](https://index.ros.org/p/nav2_simple_commander/)
(`BasicNavigator`):

| Step | Nav2 interface |
|------|----------------|
| Drive to waypoint | `goToPose()` -> `navigate_to_pose` action (`bt_navigator`) |
| Scan rotations | `spin()` -> `spin` action (`behavior_server`, collision-checked) |
| Recovery on failure | `clearAllCostmaps()` then retry |

It only needs the Nav2 servers already started by `ad_r1m_navigation`
(`planner_server`, `controller_server`, `behavior_server`, `bt_navigator`);
`waypoint_follower` is **not** required.

## Run

1. Bring up the robot (or simulation), localization and Nav2.
2. Set the robot pose in RViz with **2D Pose Estimate** (or set `set_initial_pose: true`
   in the config).
3. Edit the waypoints in [config/waypoints.yaml](config/waypoints.yaml) for your map,
   or record them in RViz (see [Recording waypoints in RViz](#recording-waypoints-in-rviz)).
4. Start the demo:

```bash
ros2 launch ad_r1m_examples waypoint_scan.launch.py \
  config:=/path/to/waypoints.yaml use_sim_time:=false

# with waypoints saved from the Nav2 RViz panel
ros2 launch ad_r1m_examples waypoint_scan.launch.py \
  waypoints_file:=/path/to/my_route.yaml

# or directly
ros2 run ad_r1m_examples waypoint_scan.py --config /path/to/waypoints.yaml
ros2 run ad_r1m_examples waypoint_scan.py --waypoints-file /path/to/my_route.yaml
```

`Ctrl+C` cancels the active Nav2 task.

## Recording waypoints in RViz

The Nav2 RViz panel can record and save waypoints without driving the robot:

1. RViz: **Panels -> Add New Panel -> nav2_rviz_plugins/Navigation 2**.
2. Click **Waypoint / Nav Through Poses Mode**.
3. Place each waypoint with the **Nav2 Goal** tool (click = position, drag = heading;
   the heading becomes the scan center). The robot does not move yet.
4. Click **Save WPs** and choose a name. The panel appends `.yaml` itself, so type
   `my_route` (typing `my_route.yaml` produces `my_route.yaml.yaml`).
5. Don't press **Start Waypoint Following** in the panel; run the demo instead with
   `waypoints_file:=/path/to/my_route.yaml` (or set `waypoints_file` in the config).

Saved format (loaded in `waypointN` order, quaternion converted to `yaw_deg`):

```yaml
waypoints:
  waypoint0:
    pose: [x, y, z]
    orientation: [w, x, y, z]
```

The file can also be reloaded in the panel with **Load WPs** to view or edit the route.
Waypoints are named `waypoint0`, `waypoint1`, ...; the `waypoints[].scan: false` option
is only available with the inline config format.

## Configuration

See [config/waypoints.yaml](config/waypoints.yaml). Key fields:

| Field | Meaning |
|-------|---------|
| `waypoints[].x/y/yaw_deg` | Goal pose in `map`; `yaw_deg` is the scan center heading |
| `waypoints[].scan` | `false` to drive through a point without scanning |
| `waypoints_file` | Nav2 RViz panel "Save WPs" file; replaces `waypoints` (relative to the config) |
| `scan.left_deg` / `scan.right_deg` | Scan amplitude on each side |
| `scan.dwell_sec` | Pause (still capturing) at left, center and right |
| `scan.return_to_center` | End the scan facing the waypoint heading |
| `loops` | Number of route repetitions (`<= 0` = forever) |
| `set_initial_pose` | `false` keeps the existing AMCL pose (recommended on the real robot) |

Spin speed and acceleration come from `behavior_server` in
`ad_r1m_navigation/config/navigation_params.yaml`
(`max_rotational_vel`, `min_rotational_vel`, `rotational_acc_lim`).

## Frame capture placeholder

`FrameCapture` in [scripts/waypoint_scan.py](scripts/waypoint_scan.py) is called:

- `start(name)` / `stop(name)` around each scan,
- `capture(name, yaw)` at `capture_rate_hz` during rotations and dwells, and forced
  once at every scan stop. `yaw` is the heading relative to the scan center (rad,
  + = left).

Replace the `TODO` in `capture()` with real camera / ToF capture.

## Notes

- Rotations are relative (odometry-based), so the robot rotates by the requested
  angle from its heading on arrival.
- `Spin` is collision-checked against the local costmap. If a rotation is blocked,
  the scan is aborted at that point and the robot tries to rotate back to center.
- With AMCL, the demo never publishes a default `(0, 0)` initial pose: it waits for
  the existing `amcl_pose` unless `set_initial_pose: true`.
