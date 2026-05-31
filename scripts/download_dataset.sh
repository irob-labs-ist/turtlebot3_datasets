#!/bin/bash
# download_dataset.sh  —  ROS 2 / rosbag2 version
# =================================================
# Downloads the turtlebot3 datasets and converts the legacy ROS 1 .bag file
# to rosbag2 format (SQLite3 or MCAP) so it can be played with `ros2 bag play`.
#
# Usage:
#   bash download_dataset.sh
#
# Prerequisites:
#   pip install gdown
#   pip install rosbags          # provides the `rosbags-convert` CLI tool

set -euo pipefail

# ── Locate the package data directory via the ament index ─────────────────────
PKG_SHARE=$(ros2 pkg prefix --share turtlebot3_datasets 2>/dev/null || true)

if [ -z "$PKG_SHARE" ]; then
    # Fallback: resolve relative to script location (useful during development)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PKG_SHARE="$(dirname "$SCRIPT_DIR")"
fi

DATA_DIR="$PKG_SHARE/data"

echo "Downloading dataset to: $DATA_DIR"
mkdir -p "$DATA_DIR"

# ── Download archive ───────────────────────────────────────────────────────────
ARCHIVE="$DATA_DIR/ir_labs.tar.gz"
gdown -O "$ARCHIVE" "https://drive.google.com/uc?id=1-QdzXIoh0ltdDNGuffLqzsPZLnLwSjAj"
tar -xvf "$ARCHIVE" -C "$DATA_DIR"

echo "Extraction complete."

# ── Convert ROS 1 .bag files to rosbag2 format ────────────────────────────────
# The `rosbags-convert` tool (from the `rosbags` Python package) reads a ROS 1
# .bag file and writes a rosbag2-compatible directory.
#
# Install with:  pip install rosbags
#
echo ""
echo "Converting ROS 1 .bag files to rosbag2 format..."

for BAG_FILE in "$DATA_DIR"/*.bag; do
    if [ ! -f "$BAG_FILE" ]; then
        echo "No .bag files found in $DATA_DIR — skipping conversion."
        break
    fi

    BAG_NAME="$(basename "$BAG_FILE" .bag)"
    OUT_DIR="$DATA_DIR/$BAG_NAME"

    if [ -d "$OUT_DIR" ]; then
        echo "  Skipping $BAG_NAME (output directory already exists)"
        continue
    fi

    echo "  Converting $BAG_FILE  ->  $OUT_DIR"
    rosbags-convert --src "$BAG_FILE" --dst "$OUT_DIR"
done

echo ""
echo "Done. Rosbag2 directories are in: $DATA_DIR"
echo ""
echo "To play a bag:"
echo "  ros2 bag play --clock $DATA_DIR/fixed_slam_easy"
