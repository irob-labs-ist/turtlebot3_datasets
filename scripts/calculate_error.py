#!/usr/bin/env python3
"""
calculate_error.py  —  ROS 2 version
=====================================
Computes the 2D localisation error in real time by comparing two TF frames:

  gt_frame  (default: 'mocap_laser_link') — ground-truth from the motion capture system
  est_frame (default: 'base_scan')        — estimated pose from the localisation algorithm

At each timer tick the node looks up the transform between the two frames and
prints the Euclidean distance (X, Y only) in millimetres.

Usage
-----
    ros2 run turtlebot3_datasets calculate_error

    # Override frames:
    ros2 run turtlebot3_datasets calculate_error \
        --ros-args -p gt_frame:=mocap_laser_link -p est_frame:=base_scan

    # Must be used with sim time when replaying a bag:
    ros2 run turtlebot3_datasets calculate_error \
        --ros-args -p use_sim_time:=true
"""

import argparse
import sys

import numpy
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException


class ErrorCalculator(Node):

    def __init__(self, gt_frame: str, est_frame: str, max_time_between: float = 0.5):
        super().__init__('evaluation_node')

        self.gt_frame  = gt_frame
        self.est_frame = est_frame

        # tf2 buffer and listener — listener requires the node as second argument in ROS 2
        self.tf_buffer   = Buffer(cache_time=Duration(seconds=max_time_between))
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Warn if sim time is not enabled
        self.declare_parameter('use_sim_time', False)
        if not self.get_parameter('use_sim_time').value:
            self.get_logger().fatal(
                'use_sim_time is False — you should run with '
                '--ros-args -p use_sim_time:=true when replaying a bag.'
            )

        # Timer at 1000 Hz (same rate as original script)
        self.create_timer(0.001, self._timer_cb)

        self.get_logger().info(
            'Listening to frames and computing error — press Ctrl-C to stop.\n'
            '  Ground-truth frame : {}\n'
            '  Estimated frame    : {}'.format(gt_frame, est_frame)
        )

    def _timer_cb(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                self.est_frame,   # target frame
                self.gt_frame,    # source frame
                Time(),           # Time() = latest available (equivalent to rospy.Time(0))
            )
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(str(e), throttle_duration_sec=2.0)
            return

        error = self._get_error(transform)
        self.get_logger().info('Error (in mm): {:.2f}'.format(error * 1e3))

    @staticmethod
    def _get_error(transform) -> float:
        """Return the 2D Euclidean distance (X, Y) from the transform translation."""
        tr = transform.transform.translation
        return float(numpy.linalg.norm([tr.x, tr.y]))


def main(args=None):
    parser = argparse.ArgumentParser(
        description='Compute real-time 2D localisation error between two TF frames.'
    )
    parser.add_argument(
        '--gt_frame',
        default='mocap_laser_link',
        help='Child frame of the ground-truth transform (default: mocap_laser_link)',
    )
    parser.add_argument(
        '--est_frame',
        default='base_scan',
        help='Child frame of the estimated pose transform (default: base_scan)',
    )

    # Strip ROS 2 arguments before parsing with argparse
    known_args, _ = parser.parse_known_args(
        [a for a in (sys.argv[1:] if args is None else args)
         if not a.startswith('--ros-args') and not a.startswith('__')]
    )

    rclpy.init(args=args)

    node = ErrorCalculator(
        gt_frame=known_args.gt_frame,
        est_frame=known_args.est_frame,
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
