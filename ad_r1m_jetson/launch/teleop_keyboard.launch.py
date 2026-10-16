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

"""Keyboard teleoperation: teleop_twist_keyboard -> twist_mux 'keyboard' input (cmd_vel_keyboard)."""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # twist_mux expects TwistStamped from Jazzy on (see ad_r1m_control/drive_control.launch.py)
    use_stamped = os.environ.get('ROS_DISTRO', 'jazzy') >= 'jazzy'

    params_file = LaunchConfiguration('params_file')
    terminal_prefix = LaunchConfiguration('terminal_prefix')

    declared_arguments = [
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_jetson'), 'config', 'teleop_keyboard.yaml']),
            description='teleop_twist_keyboard parameter file',
        ),
        DeclareLaunchArgument(
            'terminal_prefix',
            default_value='xterm -e',
            description='Terminal to run the node in (it reads keys from its own terminal)',
        ),
    ]

    parameters = [params_file]
    if not use_stamped:
        # teleop_twist_keyboard rejects frame_id when stamped is false
        parameters.append({'stamped': False, 'frame_id': ''})

    teleop_keyboard_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        prefix=terminal_prefix,
        parameters=parameters,
        remappings=[('cmd_vel', 'cmd_vel_keyboard')],
    )

    return LaunchDescription(declared_arguments + [teleop_keyboard_node])
