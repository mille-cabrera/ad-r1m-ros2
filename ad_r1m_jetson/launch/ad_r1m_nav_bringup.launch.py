# Copyright (c) 2026 Analog Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Bring up the AD-R1M navigation stack on the Jetson.

Robot base (motors + IMU + EKF) -> depth camera -> depth-to-laserscan -> SLAM Toolbox
-> Nav2 -> RViz2. Each part can be disabled with its use_* argument.

depth_source selects the depth camera feeding /scan:
  tof       - ADTF3175D ToF module (network mode, tof.launch.py)
  realsense - RealSense D435i/D435if over USB (realsense.launch.py); set the camera mount
              with mount_x/y/z/roll/pitch/yaw (see ad_r1m_perception_realsense)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    jetson_share = FindPackageShare('ad_r1m_jetson')
    jetson_launch_dir = PathJoinSubstitution([jetson_share, 'launch'])

    use_robot = LaunchConfiguration('use_robot')
    use_camera = LaunchConfiguration('use_camera')
    depth_source = LaunchConfiguration('depth_source')
    use_scan = LaunchConfiguration('use_scan')
    use_slam = LaunchConfiguration('use_slam')
    use_nav = LaunchConfiguration('use_nav')
    use_rviz = LaunchConfiguration('use_rviz')
    can_iface = LaunchConfiguration('can_iface')
    sensor_fusion = LaunchConfiguration('sensor_fusion')
    sensor_ip = LaunchConfiguration('sensor_ip')
    slam_params_file = LaunchConfiguration('slam_params_file')
    nav_params_file = LaunchConfiguration('nav_params_file')
    rviz_config = LaunchConfiguration('rviz_config')

    declared_arguments = [
        DeclareLaunchArgument('use_robot', default_value='true',
                              description='Start motors, IMU and EKF (ad_r1m_bringup)'),
        DeclareLaunchArgument('use_camera', default_value='true',
                              description='Start the driver of the selected depth camera'),
        DeclareLaunchArgument('depth_source', default_value='tof',
                              choices=['tof', 'realsense'],
                              description='Depth camera feeding /scan: tof or realsense'),
        DeclareLaunchArgument('use_scan', default_value='true',
                              description='Start the depth image to laser scan converter'),
        DeclareLaunchArgument('use_slam', default_value='true',
                              description='Start SLAM Toolbox (online async mapping)'),
        DeclareLaunchArgument('use_nav', default_value='true',
                              description='Start Nav2'),
        DeclareLaunchArgument('use_rviz', default_value='true',
                              description='Start RViz2 (needs a display)'),
        DeclareLaunchArgument('can_iface', default_value='slcan0',
                              description='CAN interface of the motor drives'),
        DeclareLaunchArgument('sensor_fusion', default_value='true',
                              description='Fuse wheel odometry and IMU with the EKF'),
        DeclareLaunchArgument('sensor_ip', default_value='192.168.56.1',
                              description='IP address of the ToF module (network mode)'),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=PathJoinSubstitution(
                [jetson_share, 'config', 'mapper_params_online_async.yaml']),
            description='SLAM Toolbox parameter file'),
        DeclareLaunchArgument(
            'nav_params_file',
            default_value=PathJoinSubstitution(
                [jetson_share, 'config', 'navigation_params.yaml']),
            description='Nav2 parameter file'),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=PathJoinSubstitution([jetson_share, 'rviz', 'ad_r1m_nav.rviz']),
            description='RViz2 configuration file'),
    ]

    # Each include is wrapped in a scoped GroupAction so that launch arguments set for
    # one include (e.g. 'params_file') do not leak into the next one.
    robot = GroupAction(
        condition=IfCondition(use_robot),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution(
                [FindPackageShare('ad_r1m_bringup'), 'launch', 'bringup.launch.py'])),
            launch_arguments={
                'can_iface': can_iface,
                'sensor_fusion': sensor_fusion,
            }.items(),
        )],
    )

    def camera_condition(source):
        return IfCondition(PythonExpression(
            ["'", use_camera, "' == 'true' and '", depth_source, "' == '", source, "'"]))

    tof = GroupAction(
        condition=camera_condition('tof'),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'tof.launch.py'])),
            launch_arguments={'sensor_ip': sensor_ip}.items(),
        )],
    )

    realsense = GroupAction(
        condition=camera_condition('realsense'),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'realsense.launch.py'])),
        )],
    )

    scan = GroupAction(
        condition=IfCondition(use_scan),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'depthimage_to_laserscan.launch.py'])),
            launch_arguments={'depth_source': depth_source}.items(),
        )],
    )

    slam = GroupAction(
        condition=IfCondition(use_slam),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'online_async_launch.py'])),
            launch_arguments={
                'params_file': slam_params_file,
                'use_sim_time': 'false',
                'autostart': 'true',
            }.items(),
        )],
    )

    nav = GroupAction(
        condition=IfCondition(use_nav),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'navigation_launch.py'])),
            launch_arguments={
                'params_file': nav_params_file,
                'use_sim_time': 'false',
                'autostart': 'true',
            }.items(),
        )],
    )

    rviz = GroupAction(
        condition=IfCondition(use_rviz),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'rviz.launch.py'])),
            launch_arguments={'rviz_config': rviz_config}.items(),
        )],
    )

    return LaunchDescription(
        declared_arguments + [robot, tof, realsense, scan, slam, nav, rviz])
