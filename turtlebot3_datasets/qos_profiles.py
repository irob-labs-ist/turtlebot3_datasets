"""
qos_profiles.py
===============
Reusable QoS profiles for turtlebot3_datasets nodes.

ROS 2 requires explicit QoS negotiation between publishers and subscribers.
Mismatches (e.g. a reliable subscriber talking to a best-effort publisher)
result in silent communication failures.  Import the correct profile here
instead of scattering QoSProfile(...) calls throughout your code.
"""

from rclpy.qos import (
    QoSProfile,
    DurabilityPolicy,
    HistoryPolicy,
    ReliabilityPolicy,
)

# ── For /tf_static  ────────────────────────────────────────────────────────────
# TRANSIENT_LOCAL (latched): late subscribers receive the last published message.
STATIC_TF_QOS = QoSProfile(
    depth=1,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
)

# ── For sensor streams (/scan, /imu, /odom, /image, …) ────────────────────────
# Best-effort with a small queue — matches typical sensor publisher defaults.
# Use this when subscribing to sensor topics from the bag.
SENSOR_QOS = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
)

# ── For navigation / odometry streams ─────────────────────────────────────────
# Reliable with a larger queue so no odometry message is silently dropped.
NAV_QOS = QoSProfile(
    depth=50,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
)

# ── Default reliable QoS (matches ROS 2 publisher defaults) ───────────────────
DEFAULT_QOS = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
)
