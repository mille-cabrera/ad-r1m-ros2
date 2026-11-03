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

Robot base (motors + IMU + EKF) -> ToF camera -> depth-to-laserscan -> SLAM Toolbox
-> Nav2 -> RViz2. Each part can be disabled with its use_* argument.

Scan source: either the ToF-derived scan (use_tof + use_scan, the default) OR the
RPLIDAR S3 (use_lidar). Both publish /scan, so enable only one path at a time, e.g.
to use the LiDAR:
    use_lidar:=true use_tof:=false use_scan:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    jetson_share = FindPackageShare('ad_r1m_jetson')
    jetson_launch_dir = PathJoinSubstitution([jetson_share, 'launch'])

    use_robot = LaunchConfiguration('use_robot')
    use_tof = LaunchConfiguration('use_tof')
    use_lidar = LaunchConfiguration('use_lidar')
    use_scan = LaunchConfiguration('use_scan')
    lidar_serial_port = LaunchConfiguration('lidar_serial_port')
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
        DeclareLaunchArgument('use_tof', default_value='true',
                              description='Start the ADTF31xx ToF camera driver'),
        DeclareLaunchArgument('use_lidar', default_value='false',
                              description='Start the RPLIDAR S3 2D LiDAR driver (publishes /scan '
                                          'directly; disable use_tof/use_scan when enabling this)'),
        DeclareLaunchArgument('use_scan', default_value='true',
                              description='Start the depth image to laser scan converter'),
        DeclareLaunchArgument('lidar_serial_port', default_value='/dev/ttyUSB0',
                              description='Serial device of the RPLIDAR S3'),
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

    tof = GroupAction(
        condition=IfCondition(use_tof),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'tof.launch.py'])),
            launch_arguments={'sensor_ip': sensor_ip}.items(),
        )],
    )

    # RPLIDAR S3 driver + a placeholder base_link -> lidar_link static transform.
    # TODO: replace the placeholder TF with the measured mount pose (ideally a URDF
    # joint in ad_r1m_description) once the LiDAR is physically mounted.
    lidar = GroupAction(
        condition=IfCondition(use_lidar),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([jetson_launch_dir, 'lidar.launch.py'])),
                launch_arguments={'serial_port': lidar_serial_port}.items(),
            ),
            Node(
                package='tf2_ros',
                executable='static_transform_publisher',
                name='base_link_to_lidar_link',
                # PLACEHOLDER pose: 0.2 m above base_link, no rotation. Measure and update.
                arguments=[
                    '--x', '-0.19', '--y', '0.0', '--z', '0.2',
                    '--roll', '0.0', '--pitch', '0.0', '--yaw', '3.14159',
                    '--frame-id', 'base_link', '--child-frame-id', 'lidar_link',
                ],
            ),
        ],
    )

    scan = GroupAction(
        condition=IfCondition(use_scan),
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([jetson_launch_dir, 'depthimage_to_laserscan.launch.py'])),
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

    return LaunchDescription(declared_arguments + [robot, tof, lidar, scan, slam, nav, rviz])
