# Copyright 2019 Open Source Robotics Foundation, Inc.
# Copyright (c) 2025-2026 Analog Devices, Inc.
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

# Author: Gary Liu
# Author: Laurentiu Popa

"""
Convert a depth image to a LaserScan (/scan) for SLAM Toolbox and Nav2.

depth_source selects the camera:
  tof       - ADTF3175D: /cam1/depth_image, /cam1/camera_info, frame cam1_scan
  realsense - RealSense: /<rs_camera_namespace>/<rs_camera_name>/depth/image_rect_raw,
              .../depth/camera_info, frame <rs_camera_name>_depth_frame
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare

DEPTH_SOURCES = ('tof', 'realsense')


def launch_setup(context, *args, **kwargs):
    namespace = LaunchConfiguration('namespace').perform(context)
    depth_source = LaunchConfiguration('depth_source').perform(context)
    param_file = LaunchConfiguration('param_file').perform(context)

    if depth_source not in DEPTH_SOURCES:
        raise RuntimeError(
            f"depth_source must be one of {DEPTH_SOURCES}, got '{depth_source}'")

    if depth_source == 'tof':
        depth_topic = '/cam1/depth_image'
        info_topic = '/cam1/camera_info'
        # TF2 frames are 'cam1_scan' or 'robot1/cam1_scan', never '/cam1_scan'
        prefix = namespace.strip('/')
        output_frame = f'{prefix}/cam1_scan' if prefix else 'cam1_scan'
        default_param_file = (FindPackageShare('ad_r1m_jetson').perform(context)
                              + '/config/depth_to_laser_params.yaml')
    else:
        rs_ns = LaunchConfiguration('rs_camera_namespace').perform(context).strip('/')
        rs_name = LaunchConfiguration('rs_camera_name').perform(context)
        rs_prefix = f'/{rs_ns}/{rs_name}' if rs_ns else f'/{rs_name}'
        depth_topic = f'{rs_prefix}/depth/image_rect_raw'
        info_topic = f'{rs_prefix}/depth/camera_info'
        # The RealSense driver does not prefix its frames with the robot namespace
        output_frame = f'{rs_name}_depth_frame'
        default_param_file = (FindPackageShare('ad_r1m_perception_realsense').perform(context)
                              + '/config/depth_to_laser_realsense.yaml')

    node_depthimage_to_laserscan = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depthimage_to_laserscan',
        remappings=[('depth', depth_topic),
                    ('depth_camera_info', info_topic),
                    ('scan', 'scan')],
        output='screen',
        parameters=[
            param_file or default_param_file,
            {'output_frame': output_frame}
        ]
    )

    return [GroupAction([
        PushRosNamespace(namespace),
        node_depthimage_to_laserscan
    ])]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Robot namespace for multi-robot systems (e.g., robot1, robot2)',
        ),
        DeclareLaunchArgument(
            'depth_source',
            default_value='tof',
            choices=list(DEPTH_SOURCES),
            description='Depth camera feeding the scan: tof (ADTF3175D) or realsense (D435if)',
        ),
        DeclareLaunchArgument(
            'param_file',
            default_value='',
            description='depthimage_to_laserscan parameter file (empty = depth_source default)',
        ),
        DeclareLaunchArgument(
            'rs_camera_namespace',
            default_value='camera',
            description='RealSense camera namespace (depth_source realsense)',
        ),
        DeclareLaunchArgument(
            'rs_camera_name',
            default_value='camera',
            description='RealSense camera name / TF frame prefix (depth_source realsense)',
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
