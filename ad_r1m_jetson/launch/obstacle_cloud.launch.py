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
Downsample the depth camera point cloud into /obstacle_cloud for 3D obstacles in Nav2.

The Nav2 costmaps use /obstacle_cloud (PointCloud2) next to /scan, so obstacles above or
below the scan band (table tops, overhangs, low objects) are marked too.

depth_source selects the input:
  tof       - ADTF3175D driver cloud /cam1/point_cloud (param_enable_point_cloud_publish: true)
  realsense - depth_image_proc PointCloudXyzNode on the RealSense depth image
              /<rs_camera_namespace>/<rs_camera_name>/depth/image_rect_raw (+ camera_info)
              -> /<rs_camera_namespace>/<rs_camera_name>/depth/points
cloud_topic overrides the input cloud topic (and skips depth_image_proc).

The nodes run in one component container with intra-process communication, so the
full-resolution cloud is not serialized between depth_image_proc and the filter.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, PushRosNamespace
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare

DEPTH_SOURCES = ('tof', 'realsense')
INTRA_PROCESS = [{'use_intra_process_comms': True}]


def launch_setup(context, *args, **kwargs):
    namespace = LaunchConfiguration('namespace').perform(context)
    depth_source = LaunchConfiguration('depth_source').perform(context)
    cloud_topic = LaunchConfiguration('cloud_topic').perform(context)

    if depth_source not in DEPTH_SOURCES:
        raise RuntimeError(
            f"depth_source must be one of {DEPTH_SOURCES}, got '{depth_source}'")

    nodes = []
    if not cloud_topic:
        if depth_source == 'tof':
            cloud_topic = '/cam1/point_cloud'
        else:
            rs_ns = LaunchConfiguration('rs_camera_namespace').perform(context).strip('/')
            rs_name = LaunchConfiguration('rs_camera_name').perform(context)
            rs_prefix = f'/{rs_ns}/{rs_name}' if rs_ns else f'/{rs_name}'
            cloud_topic = f'{rs_prefix}/depth/points'
            # camera_info is taken from the image topic's namespace: <rs_prefix>/depth/camera_info
            nodes.append(ComposableNode(
                package='depth_image_proc',
                plugin='depth_image_proc::PointCloudXyzNode',
                name='obstacle_cloud_xyz',
                remappings=[('image_rect', f'{rs_prefix}/depth/image_rect_raw'),
                            ('points', cloud_topic)],
                extra_arguments=INTRA_PROCESS,
            ))

    nodes.append(ComposableNode(
        package='pcl_ros',
        plugin='pcl_ros::VoxelGrid',
        name='obstacle_cloud_filter',
        remappings=[('input', cloud_topic),
                    ('output', 'obstacle_cloud')],
        parameters=[LaunchConfiguration('param_file')],
        extra_arguments=INTRA_PROCESS,
    ))

    container = ComposableNodeContainer(
        name='obstacle_cloud_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=nodes,
        output='screen',
    )

    return [GroupAction([
        PushRosNamespace(namespace),
        container,
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
            description='Depth camera providing the cloud: tof (ADTF3175D) or realsense (D435if)',
        ),
        DeclareLaunchArgument(
            'cloud_topic',
            default_value='',
            description='Input PointCloud2 topic (empty = depth_source default)',
        ),
        DeclareLaunchArgument(
            'param_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('ad_r1m_jetson'), 'config', 'obstacle_cloud_params.yaml']),
            description='pcl_ros VoxelGrid parameter file',
        ),
        DeclareLaunchArgument(
            'rs_camera_namespace',
            default_value='camera',
            description='RealSense camera namespace (depth_source realsense)',
        ),
        DeclareLaunchArgument(
            'rs_camera_name',
            default_value='camera',
            description='RealSense camera name (depth_source realsense)',
        ),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
