#!/bin/bash
# download_dataset.sh  —  ROS 2 / rosbag2 version
# =================================================
# Downloads the turtlebot rosbag2 datasets (already in rosbag2 format,
# no conversion needed) so they can be played directly with `ros2 bag play`.
#
# Usage:
#   bash download_dataset.sh
#
# Prerequisites:
#   pip install gdown

set -euo pipefail

# ── Locate the package data directory via the ament index ─────────────────────
PKG_SHARE=$(ros2 pkg prefix --share turtlebot_datasets 2>/dev/null || true)

if [ -z "$PKG_SHARE" ]; then
    # Fallback: resolve relative to script location (useful during development)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PKG_SHARE="$(dirname "$SCRIPT_DIR")"
fi

DATA_DIR="$PKG_SHARE/data"

echo "Downloading dataset to: $DATA_DIR"
mkdir -p "$DATA_DIR"

# ── Download archive ───────────────────────────────────────────────────────────
ARCHIVE="$DATA_DIR/ir_labData.tar.xz"
gdown -O "$ARCHIVE" "https://drive.google.com/uc?id=1Kk3tMdPU2ve3PdhCKxfvijTVc8OXlbAY"
tar -xvf "$ARCHIVE" -C "$DATA_DIR" --strip-components=1

echo ""
echo "Done. Rosbag2 directories are in: $DATA_DIR"
echo ""
echo "To play a bag:"
echo "  ros2 bag play --clock $DATA_DIR/fixed_slam_easy"
