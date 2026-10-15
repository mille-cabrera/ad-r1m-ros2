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
Launch the RealSense D435i/D435if depth camera (depth only) and its mount TF.

Counterpart of tof.launch.py. Arguments (camera_namespace, camera_name, params_file, serial_no,
publish_mount_tf, parent_frame, mount_x/y/z/roll/pitch/yaw) are those of
ad_r1m_perception_realsense/launch/realsense.launch.py.
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare('ad_r1m_perception_realsense'), 'launch',
                'realsense.launch.py'])),
        ),
    ])
