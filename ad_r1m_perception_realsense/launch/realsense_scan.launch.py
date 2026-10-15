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

"""RealSense depth camera + depth image to laser scan (/scan) for SLAM Toolbox."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('ad_r1m_perception_realsense')

    use_camera = LaunchConfiguration('use_camera')
    camera_namespace = LaunchConfiguration('camera_namespace')
    camera_name = LaunchConfiguration('camera_name')
    scan_params_file = LaunchConfiguration('scan_params_file')
    scan_topic = LaunchConfiguration('scan_topic')

    declared_arguments = [
        DeclareLaunchArgument(
            'use_camera', default_value='true',
            description='Start the RealSense driver (false = convert an existing stream/bag)'),
        DeclareLaunchArgument('camera_namespace', default_value='camera'),
        DeclareLaunchArgument('camera_name', default_value='camera'),
        DeclareLaunchArgument(
            'scan_params_file',
            default_value=PathJoinSubstitution(
                [pkg_share, 'config', 'depth_to_laser_realsense.yaml']),
            description='depthimage_to_laserscan parameter file'),
        DeclareLaunchArgument('scan_topic', default_value='scan',
                              description='Output LaserScan topic'),
    ]

    camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, 'launch', 'realsense.launch.py'])),
        condition=IfCondition(use_camera),
    )

    depth_to_scan = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depthimage_to_laserscan',
        output='screen',
        remappings=[
            ('depth', ['/', camera_namespace, '/', camera_name, '/depth/image_rect_raw']),
            ('depth_camera_info', ['/', camera_namespace, '/', camera_name, '/depth/camera_info']),
            ('scan', scan_topic),
        ],
        parameters=[
            scan_params_file,
            {'output_frame': [camera_name, '_depth_frame']},
        ],
    )

    return LaunchDescription(declared_arguments + [camera, depth_to_scan])
