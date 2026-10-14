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

"""Launch the ADTF31xx ToF camera driver in network mode (EVAL-ADTF3175D-NXZ)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    camera_namespace = LaunchConfiguration('camera_namespace')
    params_file = LaunchConfiguration('params_file')
    sensor_ip = LaunchConfiguration('sensor_ip')
    sdk_config_file = LaunchConfiguration('sdk_config_file')

    declared_arguments = [
        DeclareLaunchArgument(
            'camera_namespace',
            default_value='cam1',
            description='Namespace of the ToF camera topics (e.g. /cam1/depth_image)',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_jetson'), 'config', 'tof_adtf31xx.yaml']),
            description='Path to the ToF driver parameter file',
        ),
        DeclareLaunchArgument(
            'sensor_ip',
            default_value='192.168.56.1',
            description='IP address of the ToF module (network mode)',
        ),
        DeclareLaunchArgument(
            'sdk_config_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('adi_3dtof_adtf31xx'), 'config',
                'config_adsd3500_adsd3100.json']),
            description='ToF SDK camera configuration JSON',
        ),
    ]

    tof_node = Node(
        package='adi_3dtof_adtf31xx',
        executable='adi_3dtof_adtf31xx_node',
        name='adi_3dtof_adtf31xx_node',
        namespace=camera_namespace,
        output='screen',
        parameters=[
            params_file,
            {
                'param_input_sensor_ip': sensor_ip,
                'param_config_file_name_of_tof_sdk': sdk_config_file,
            },
        ],
    )

    return LaunchDescription(declared_arguments + [tof_node])
