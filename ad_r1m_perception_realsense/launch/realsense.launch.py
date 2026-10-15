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
Launch the RealSense D435i/D435if driver (depth only) and its mount TF.

TF: <parent_frame> -> <camera_name>_link is published here (mount pose arguments);
<camera_name>_link -> <camera_name>_depth_frame -> <camera_name>_depth_optical_frame is
published by the driver from the camera's factory extrinsics.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    camera_namespace = LaunchConfiguration('camera_namespace')
    camera_name = LaunchConfiguration('camera_name')
    params_file = LaunchConfiguration('params_file')
    serial_no = LaunchConfiguration('serial_no')
    publish_mount_tf = LaunchConfiguration('publish_mount_tf')
    parent_frame = LaunchConfiguration('parent_frame')

    # Defaults place camera_link at the ADTF3175D ToF mount of ad_r1m_base.urdf.xacro
    # (front of chassis, level). Measure the real mount and override.
    mount_defaults = {
        'mount_x': '0.2755',
        'mount_y': '0.0',
        'mount_z': '0.06',
        'mount_roll': '0.0',
        'mount_pitch': '0.0',
        'mount_yaw': '0.0',
    }

    declared_arguments = [
        DeclareLaunchArgument(
            'camera_namespace', default_value='camera',
            description='Namespace of the camera node (topics: /<namespace>/<name>/...)'),
        DeclareLaunchArgument(
            'camera_name', default_value='camera',
            description='Camera node name; also the TF frame prefix (<name>_link, ...)'),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_perception_realsense'), 'config',
                'realsense_d435if.yaml']),
            description='realsense2_camera parameter file'),
        DeclareLaunchArgument(
            'serial_no', default_value='',
            description='Camera serial number (empty = first device found)'),
        DeclareLaunchArgument(
            'publish_mount_tf', default_value='true',
            description='Publish <parent_frame> -> <camera_name>_link (false if the URDF has it)'),
        DeclareLaunchArgument(
            'parent_frame', default_value='base_link',
            description='Frame the camera is mounted on'),
    ] + [
        DeclareLaunchArgument(
            name, default_value=value,
            description=f'Camera mount {name.split("_")[1]} of <camera_name>_link in '
                        '<parent_frame> (m / rad)')
        for name, value in mount_defaults.items()
    ]

    realsense_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        name=camera_name,
        namespace=camera_namespace,
        output='screen',
        emulate_tty=True,
        parameters=[
            params_file,
            {
                'camera_name': camera_name,
                'serial_no': ParameterValue(serial_no, value_type=str),
            },
        ],
    )

    mount_tf_node = Node(
        condition=IfCondition(publish_mount_tf),
        package='tf2_ros',
        executable='static_transform_publisher',
        name=[camera_name, '_mount_tf'],
        output='screen',
        arguments=[
            '--x', LaunchConfiguration('mount_x'),
            '--y', LaunchConfiguration('mount_y'),
            '--z', LaunchConfiguration('mount_z'),
            '--roll', LaunchConfiguration('mount_roll'),
            '--pitch', LaunchConfiguration('mount_pitch'),
            '--yaw', LaunchConfiguration('mount_yaw'),
            '--frame-id', parent_frame,
            '--child-frame-id', [camera_name, '_link'],
        ],
    )

    return LaunchDescription(declared_arguments + [realsense_node, mount_tf_node])
