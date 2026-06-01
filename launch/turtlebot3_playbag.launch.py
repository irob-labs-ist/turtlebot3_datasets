"""
Launch file for playing a turtlebot3 rosbag2 dataset.

Before launching:
    1. Edit the `bag_path` variable below to point to your rosbag2 directory.

Usage:
    ros2 launch turtlebot3_datasets turtlebot3_playbag.launch.py
    ros2 launch turtlebot3_datasets turtlebot3_playbag.launch.py model:=waffle_pi
    ros2 launch turtlebot3_datasets turtlebot3_playbag.launch.py viz:=foxglove
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = get_package_share_directory('turtlebot3_datasets')

    # ---------------------------------------------------------------------------
    # Launch arguments
    # ---------------------------------------------------------------------------
    model_arg = DeclareLaunchArgument(
        'model',
        default_value='waffle_pi',
        description='Turtlebot3 model (burger | waffle | waffle_pi)',
    )

    viz_arg = DeclareLaunchArgument(
        'viz',
        default_value='rviz2',
        description='Visualisation tool to launch: rviz2 | foxglove',
    )

    fixed_frame_arg = DeclareLaunchArgument(
        'fixed_frame',
        default_value='odom',
        description='Fixed frame to connect mocap to (odom | map | ...)',
    )

    # ---------------------------------------------------------------------------
    # Set TURTLEBOT3_MODEL environment variable from the 'model' argument.
    # turtlebot3_remote.launch.py reads this env var — without it the URDF
    # cannot be loaded and the launch will fail.
    # ---------------------------------------------------------------------------
    set_turtlebot3_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value=LaunchConfiguration('model'),
    )

    # ---------------------------------------------------------------------------
    # Turtlebot3 remote (URDF / robot_state_publisher + joint_state_publisher)
    # ---------------------------------------------------------------------------
    turtlebot3_bringup_share = FindPackageShare('turtlebot3_bringup')

    turtlebot3_remote = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            turtlebot3_bringup_share, '/launch/turtlebot3_remote.launch.py'
        ]),
        launch_arguments={'model': LaunchConfiguration('model')}.items(),
    )

    # ---------------------------------------------------------------------------
    # Rosbag2 playback  (replaces `rosbag play --clock ...`)
    # use_sim_time is handled per-node; the bag publishes /clock automatically
    # when --clock is passed.
    #
    # !! INSERT THE FULL PATH TO YOUR BAG DIRECTORY BELOW !!
    # Example: '/home/user/ros2_ws/src/turtlebot3_datasets/data/fixed_slam_easy'
    # ---------------------------------------------------------------------------
    bag_path = '/INSERT/BAG/PATH/HERE'

    rosbag_play = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'play',
            '--clock',          # publish /clock so nodes can use sim time
            '--rate', '1.0',    # playback speed multiplier (change as needed)
            bag_path,
        ],
        output='screen',
    )

    # ---------------------------------------------------------------------------
    # Map server  (uncomment and configure when you have a map)
    # ---------------------------------------------------------------------------
    # map_file = os.path.join(pkg_share, 'data', 'map.yaml')
    # map_server = Node(
    #     package='nav2_map_server',
    #     executable='map_server',
    #     name='map_server',
    #     parameters=[{'yaml_filename': map_file, 'use_sim_time': True}],
    # )
    # nav2_lifecycle_manager for map_server:
    # Node(
    #     package='nav2_lifecycle_manager',
    #     executable='lifecycle_manager',
    #     name='lifecycle_manager_map',
    #     parameters=[{
    #         'use_sim_time': True,
    #         'autostart': True,
    #         'node_names': ['map_server'],
    #     }],
    # )

    # ---------------------------------------------------------------------------
    # Static TF: mocap -> odom  (publishes the initial ground-truth transform)
    # Can also be launched separately via:
    #   ros2 run turtlebot3_datasets publish_initial_tf odom
    # ---------------------------------------------------------------------------
    publish_initial_tf = Node(
        package='turtlebot3_datasets',
        executable='publish_initial_tf',
        name='publish_initial_tf',
        parameters=[{'use_sim_time': True}],
        arguments=[LaunchConfiguration('fixed_frame')],
    )

    # ---------------------------------------------------------------------------
    # EKF robot localisation  (uncomment when using robot_localization)
    # ---------------------------------------------------------------------------
    # ekf_config = os.path.join(pkg_share, 'config', 'ekf.yaml')
    # ekf_node = Node(
    #     package='robot_localization',
    #     executable='ekf_node',
    #     name='ekf_filter_node',
    #     parameters=[ekf_config, {'use_sim_time': True}],
    # )

    # ---------------------------------------------------------------------------
    # AMCL  (uncomment when using AMCL localisation)
    # ---------------------------------------------------------------------------
    # amcl_node = Node(
    #     package='nav2_amcl',
    #     executable='amcl',
    #     name='amcl',
    #     parameters=[{'use_sim_time': True}],
    # )

    # ---------------------------------------------------------------------------
    # Visualisation — chose an option for 'viz':
    #
    #   ros2 launch turtlebot3_datasets turtlebot3_playbag.launch.py viz:=rviz2
    #   ros2 launch turtlebot3_datasets turtlebot3_playbag.launch.py viz:=foxglove
    #
    # ---------------------------------------------------------------------------

    # Opção A: RViz2
    rviz_config = os.path.join(pkg_share, 'config', 'rviz2_config.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('viz'), "' == 'rviz2'"])
        ),
    )

    # Opção B: Foxglove
    # (WebSocket server at ws://localhost:8765)
    #  
    #
    # Installation: sudo apt install ros-$ROS_DISTRO-foxglove-bridge
    foxglove_bridge = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        name='foxglove_bridge',
        parameters=[{'use_sim_time': True}],
        output='screen',
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('viz'), "' == 'foxglove'"])
        ),
    )

    foxglove_browser = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=['xdg-open', 'https://app.foxglove.dev'],
                output='screen',
            )
        ],
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration('viz'), "' == 'foxglove'"])
        ),
    )

    # ---------------------------------------------------------------------------
    # Assemble description
    # ---------------------------------------------------------------------------
    return LaunchDescription([
        model_arg,
        viz_arg,
        fixed_frame_arg,
        set_turtlebot3_model,
        turtlebot3_remote,
        rosbag_play,
        rviz_node,
        foxglove_bridge,
        foxglove_browser,
        publish_initial_tf,
        # Uncomment nodes above as needed:
        # map_server,
        # ekf_node,
        # amcl_node,
    ])
