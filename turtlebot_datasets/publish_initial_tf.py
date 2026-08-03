#!/usr/bin/env python3
"""
publish_initial_tf.py  —  ROS 2 version
========================================
Publishes the static transform  mocap -> <fixed_frame>  that connects the
motion-capture reference frame to the robot's fixed frame (odom, map, …).

This replaces the ROS 1 shell script that called:
    rosrun tf2_ros static_transform_publisher x y z qx qy qz qw parent child

Usage (as a ROS 2 node):
    ros2 run turtlebot_datasets publish_initial_tf -- odom
    ros2 run turtlebot_datasets publish_initial_tf -- map

The transform values below were measured at the beginning of the dataset:
    translation:  x=0.935  y=1.340  z=-0.023
    rotation:     qx=0.001 qy=-0.003 qz=0.737 qw=0.676
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage


# ── Hard-coded initial transform (mocap -> fixed_frame) ───────────────────────
TRANSLATION_X =  0.935
TRANSLATION_Y =  1.340
TRANSLATION_Z = -0.023
ROTATION_QX   =  0.001
ROTATION_QY   = -0.003
ROTATION_QZ   =  0.737
ROTATION_QW   =  0.676
# ─────────────────────────────────────────────────────────────────────────────


class InitialTFPublisher(Node):
    """
    Publishes a latched static transform on /tf_static.

    ROS 2 uses a TRANSIENT_LOCAL QoS for /tf_static so that late-joining
    subscribers receive the last published message immediately (equivalent to
    a latched publisher in ROS 1).
    """

    def __init__(self, fixed_frame: str) -> None:
        super().__init__('publish_initial_tf')

        # TRANSIENT_LOCAL = latched publisher (new subscribers get last message)
        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
        )

        self._pub = self.create_publisher(TFMessage, '/tf_static', qos)

        ts = TransformStamped()
        ts.header.stamp = self.get_clock().now().to_msg()
        ts.header.frame_id = 'mocap'
        ts.child_frame_id  = fixed_frame

        ts.transform.translation.x = TRANSLATION_X
        ts.transform.translation.y = TRANSLATION_Y
        ts.transform.translation.z = TRANSLATION_Z
        ts.transform.rotation.x    = ROTATION_QX
        ts.transform.rotation.y    = ROTATION_QY
        ts.transform.rotation.z    = ROTATION_QZ
        ts.transform.rotation.w    = ROTATION_QW

        msg = TFMessage(transforms=[ts])
        self._pub.publish(msg)

        self.get_logger().info(
            'Published static TF: mocap -> {} '
            '(t=[{:.3f}, {:.3f}, {:.3f}]  q=[{:.3f}, {:.3f}, {:.3f}, {:.3f}])'.format(
                fixed_frame,
                TRANSLATION_X, TRANSLATION_Y, TRANSLATION_Z,
                ROTATION_QX,   ROTATION_QY,   ROTATION_QZ,   ROTATION_QW,
            )
        )


def main(args=None):
    rclpy.init(args=args)

    # Determine the target fixed frame from command-line arguments
    argv = sys.argv[1:]  # strip the node name if present
    if not argv:
        print('Usage: publish_initial_tf <fixed_frame>  (e.g. odom | map)')
        print('Defaulting to: odom')
        fixed_frame = 'odom'
    else:
        fixed_frame = argv[0]

    node = InitialTFPublisher(fixed_frame)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
