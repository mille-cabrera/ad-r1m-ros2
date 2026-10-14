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

"""Gamepad teleoperation: joy/game_controller_node -> teleop_twist_joy -> twist_mux 'joy' input."""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Same convention as ad_r1m_control/drive_control.launch.py: twist_mux expects
    # TwistStamped on cmd_vel_joy from Jazzy on, and Twist on cmd_vel_joy_unstamped before.
    use_stamped = os.environ.get('ROS_DISTRO', 'jazzy') >= 'jazzy'
    cmd_vel_topic = 'cmd_vel_joy' if use_stamped else 'cmd_vel_joy_unstamped'

    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    device_id = LaunchConfiguration('device_id')

    declared_arguments = [
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_teleop_joy'), 'config', 'logitech_f310.yaml']),
            description='Gamepad parameter file',
        ),
        DeclareLaunchArgument(
            'device_id',
            default_value='0',
            description='SDL joystick index (list with: ros2 run joy joy_enumerate_devices)',
        ),
    ]

    joy_node = Node(
        package='joy',
        executable='game_controller_node',
        name='game_controller_node',
        output='screen',
        parameters=[params_file, {'device_id': device_id}],
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        output='screen',
        parameters=[params_file, {'publish_stamped_twist': use_stamped}],
        remappings=[('cmd_vel', cmd_vel_topic)],
    )

    return LaunchDescription(declared_arguments + [
        GroupAction([
            PushRosNamespace(namespace),
            joy_node,
            teleop_node,
        ]),
    ])
