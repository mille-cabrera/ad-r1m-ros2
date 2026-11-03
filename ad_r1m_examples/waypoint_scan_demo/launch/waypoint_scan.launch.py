import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory('ad_r1m_examples'),
        'waypoint_scan_demo', 'config', 'waypoints.yaml')

    config = LaunchConfiguration('config')
    waypoints_file = LaunchConfiguration('waypoints_file')
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config', default_value=default_config,
            description='Waypoints + scan YAML file'),
        DeclareLaunchArgument(
            'waypoints_file', default_value='',
            description='Waypoints saved with the Nav2 RViz panel "Save WPs" (overrides config)'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Robot namespace (must match the Nav2 namespace)'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation clock'),
        Node(
            package='ad_r1m_examples',
            executable='waypoint_scan.py',
            output='screen',
            emulate_tty=True,
            arguments=[['--config=', config], ['--waypoints-file=', waypoints_file],
                       ['--namespace=', namespace]],
            parameters=[{'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
        ),
    ])
