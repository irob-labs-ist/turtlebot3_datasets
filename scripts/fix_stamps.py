#!/usr/bin/env python3
"""
fix_stamps.py  —  ROS 2 / rosbag2 version
==========================================
Fix a specific TF time-stamp offset in a rosbag2 bag.

The script works on bags where a constant time difference exists between the
robot TF tree and the motion-capture TF tree.  It reads every message from the
input bag, adjusts the stamps of any /tf transform whose *parent* frame matches
PARENT_FRAME, and writes the corrected messages to a new bag.

For messages that carry a header the recorded *bag* timestamp is replaced by
the message's own header.stamp (this is what the original ROS 1 script did).

Usage
-----
    python3 fix_stamps.py TIME_OFFSET INPUT_BAG_DIR OUTPUT_BAG_DIR

Example (slam_easy.bag — measured offset ≈ 3961.46 s):
    python3 fix_stamps.py 3961.461462163 slam_easy fixed_slam_easy

Dependencies
------------
    pip install rosbag2_py rclpy

Notes
-----
* Input and output are *directories* (rosbag2 format), not single .bag files.
* The default storage plugin is 'sqlite3'; change STORAGE_ID if your bag uses
  a different backend (e.g. 'mcap').
* tf2_msgs/TFMessage replaces the ROS 1 tf/tfMessage type.
"""

import sys
import os

try:
    import rosbag2_py
except ImportError:
    sys.exit(
        "rosbag2_py not found.\n"
        "Install it with:  pip install rosbag2_py\n"
        "or via apt:       sudo apt install ros-$ROS_DISTRO-rosbag2"
    )

from rclpy.serialization import deserialize_message, serialize_message
from rclpy.time import Duration
from rosidl_runtime_py.utilities import get_message

# ── Configuration ──────────────────────────────────────────────────────────────
PARENT_FRAME = 'mocap'
STORAGE_ID   = 'sqlite3'   # or 'mcap'
# ───────────────────────────────────────────────────────────────────────────────


def make_reader(bag_dir: str) -> rosbag2_py.SequentialReader:
    reader = rosbag2_py.SequentialReader()
    storage_opts = rosbag2_py.StorageOptions(uri=bag_dir, storage_id=STORAGE_ID)
    conv_opts    = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr',
    )
    reader.open(storage_opts, conv_opts)
    return reader


def make_writer(bag_dir: str) -> rosbag2_py.SequentialWriter:
    writer = rosbag2_py.SequentialWriter()
    storage_opts = rosbag2_py.StorageOptions(uri=bag_dir, storage_id=STORAGE_ID)
    conv_opts    = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr',
    )
    writer.open(storage_opts, conv_opts)
    return writer


def ns_from_sec(sec: float) -> int:
    """Convert floating-point seconds to integer nanoseconds."""
    return int(sec * 1e9)


def main():
    if len(sys.argv) < 4:
        print('Usage: {} TIME_OFFSET INPUT_BAG_DIR OUTPUT_BAG_DIR'.format(sys.argv[0]))
        sys.exit(1)

    offset_sec  = float(sys.argv[1])
    in_bag_dir  = sys.argv[2]
    out_bag_dir = sys.argv[3]

    offset_ns = ns_from_sec(offset_sec)

    print('Applying offset of {:f} s to frames whose parent is "{}"'.format(
        offset_sec, PARENT_FRAME))
    print('Input  bag: {}'.format(in_bag_dir))
    print('Output bag: {}'.format(out_bag_dir))

    # ── Open reader ────────────────────────────────────────────────────────────
    reader = make_reader(in_bag_dir)
    topic_types = reader.get_all_topics_and_types()

    # Build a map: topic_name -> message_type_string
    type_map = {t.name: t.type for t in topic_types}

    # ── Open writer and register all topics ────────────────────────────────────
    writer = make_writer(out_bag_dir)
    for t in topic_types:
        writer.create_topic(t)

    # ── Progress bar (optional) ─────────────────────────────────────────────────
    try:
        import progressbar
        total = reader.get_metadata().message_count
        bar = progressbar.ProgressBar(max_value=total, redirect_stdout=True)
    except Exception:
        print("Tip: install progressbar2 for a progress indicator:  pip install progressbar2")
        bar = None

    msg_counter = 0

    # ── Main loop ───────────────────────────────────────────────────────────────
    while reader.has_next():
        topic, raw_data, bag_ts_ns = reader.read_next()
        msg_counter += 1
        if bar:
            bar.update(msg_counter)

        msg_type_str = type_map.get(topic)
        MsgClass = get_message(msg_type_str)
        msg = deserialize_message(raw_data, MsgClass)

        if topic == '/tf':
            # tf2_msgs/TFMessage
            for transform in msg.transforms:
                if transform.header.frame_id == PARENT_FRAME:
                    # Subtract the offset from the stamp
                    stamp_ns = (
                        transform.header.stamp.sec * 10**9
                        + transform.header.stamp.nanosec
                        - offset_ns
                    )
                    transform.header.stamp.sec     = stamp_ns // 10**9
                    transform.header.stamp.nanosec = stamp_ns  % 10**9

            # Use the stamp of the first transform as the bag timestamp
            first = msg.transforms[0].header.stamp
            out_ts_ns = first.sec * 10**9 + first.nanosec
            writer.write(topic, serialize_message(msg), out_ts_ns)

        elif hasattr(msg, 'header'):
            # Any message with a header: use header.stamp as bag timestamp
            out_ts_ns = msg.header.stamp.sec * 10**9 + msg.header.stamp.nanosec
            writer.write(topic, serialize_message(msg), out_ts_ns)

        else:
            # No header: keep original bag timestamp
            writer.write(topic, raw_data, bag_ts_ns)

    if bar:
        bar.finish()

    print('\nDone. Processed {} messages.'.format(msg_counter))
    print('Output written to: {}'.format(out_bag_dir))


if __name__ == '__main__':
    main()
