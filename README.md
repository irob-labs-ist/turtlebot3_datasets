# turtlebot_datasets — ROS 2

This package provides helper scripts to download and use datasets for the **Introduction to Robotics** labs.

The datasets were captured on a [Turtlebot 3 Waffle Pi](http://www.robotis.us/turtlebot-3-waffle-pi/).

## Dataset information

A map and rosbag are provided along with some helper scripts.

The initial bag had a synchronization issue. This has been fixed using [fix_stamps.py](scripts/fix_stamps.py).

The fixed bag includes (use `ros2 bag info fixed_slam_easy` to inspect it):

```
topics:      /imu                              14805 msgs    : sensor_msgs/msg/Imu
             /odom                              3252 msgs    : nav_msgs/msg/Odometry
             /raspicam_node/camera_info         1814 msgs    : sensor_msgs/msg/CameraInfo
             /raspicam_node/image/compressed    1811 msgs    : sensor_msgs/msg/CompressedImage
             /scan                               626 msgs    : sensor_msgs/msg/LaserScan
             /tf                               21329 msgs    : tf2_msgs/msg/TFMessage
             /tf_static                            1 msg     : tf2_msgs/msg/TFMessage
```

The setup includes ground-truth data obtained from a [motion capture system](http://welcome.isr.tecnico.ulisboa.pt/isrobonet/) at 60 Hz. Five markers were placed on the top layer of the robot, such that the centre of the tracked object matched the laser scanner of the robot.

The ground-truth data is provided in the `/tf` topic, as a transform `mocap -> mocap_laser_link`. To conform to [REP 105](http://www.ros.org/reps/rep-0105.html), the initial transform was obtained at the robot's base footprint frame. The homogeneous transformation matrix at the beginning of the dataset is given by:

![transform](docs/gt_transform.svg)

The initial transform can be used to connect `mocap` to `odom`, `map`, or another fixed frame. This is done by running [publish_initial_tf](turtlebot_datasets/publish_initial_tf.py):

```bash
ros2 run turtlebot_datasets publish_initial_tf -- odom   # or map, etc.
```

Images `docs/unconnected_tree.svg` and `docs/connected_tree.svg` show the frame setup before and after adding the `mocap -> odom` transform. These can be regenerated with:

```bash
ros2 run tf2_tools view_frames
```

The map was obtained using [turtlebot3_cartographer](https://emanual.robotis.com/docs/en/platform/turtlebot3/slam/#run-slam-node) with default parameters.

---

## Notes

A few things to be aware of before starting:

- **Simulation time** — when replaying a bag, nodes must use the `/clock` topic published by the bag player instead of wall-clock time. Each node that needs sim time must be launched with `use_sim_time:=true`. The launch file already sets this for rviz2 and other nodes it launches.

- **Always play the bag with `--clock`** — this publishes the `/clock` topic. You can also use `--rate RATE` to speed up or slow down playback, and `--start-offset SECONDS` to jump into the bag.

- **QoS profiles** — ROS 2 requires publishers and subscribers to agree on a QoS policy. If a node is not receiving sensor data from the bag, the most common cause is a QoS mismatch. Check [`turtlebot_datasets/qos_profiles.py`](turtlebot_datasets/qos_profiles.py) for the profiles used in this package.

- More information on the `ros2 bag` tool: `ros2 bag --help`

---

## Steps

### 1. Install system prerequisites

```bash
sudo apt update
sudo apt install python3-pip python3-rosbag2 ros-$ROS_DISTRO-rosbag2 \
                 ros-$ROS_DISTRO-turtlebot3-bringup ros-$ROS_DISTRO-rviz2 \
                 ros-$ROS_DISTRO-foxglove-bridge   # optional, only needed for viz:=foxglove
```

Set the Turtlebot model environment variable — this is required before any `ros2 launch` command. Add it to your `~/.bashrc` so it persists across terminals:

```bash
echo "export TURTLEBOT3_MODEL=waffle_pi" >> ~/.bashrc
source ~/.bashrc
```

### 2. Install Python prerequisites

```bash
pip install gdown
```

### 3. Clone and build the package

```bash
# Clone into the src directory of your ROS 2 workspace
cd ~/ros2_ws/src
git clone https://github.com/irob-labs-ist/datasets.git

# Build with colcon (replaces catkin_make)
cd ~/ros2_ws
colcon build --packages-select turtlebot_datasets

# Source the workspace overlay (replaces source devel/setup.bash)
source install/setup.bash
```

### 4. Download the dataset

```bash
cd ~/ros2_ws/src/datasets/scripts
bash download_dataset.sh
```

This downloads the archive and extracts the rosbag2 directories into the `data/` folder, ready to use directly with `ros2 bag play`.

### 5. Publish the initial static transform

This connects the motion-capture reference frame (`mocap`) to the robot's fixed frame (`odom`, `map`, …). Run it in a separate terminal:

```bash
ros2 run turtlebot_datasets publish_initial_tf -- odom
# replace 'odom' with 'map' or another fixed frame as needed
```

You can also add this as a node directly inside [turtlebot_playbag.launch.py](launch/turtlebot_playbag.launch.py) by uncommenting the `publish_initial_tf` block.

### 6. Edit the bag path and launch

Before launching, open [launch/turtlebot_playbag.launch.py](launch/turtlebot_playbag.launch.py) and set the `bag_path` variable to the full path of your rosbag2 directory:

```python
# inside turtlebot_playbag.launch.py
bag_path = '/home/<user>/ros2_ws/src/turtlebot_datasets/data/fixed_slam_easy'
```

Then launch:

```bash
# RViz2 (default)
ros2 launch turtlebot_datasets turtlebot_playbag.launch.py

# Foxglove (opens browser at app.foxglove.dev — connect to ws://localhost:8765)
ros2 launch turtlebot_datasets turtlebot_playbag.launch.py viz:=foxglove

# Change robot model if needed
ros2 launch turtlebot_datasets turtlebot_playbag.launch.py model:=burger
```

This launches:
- `turtlebot3_remote.launch.py` (robot model / URDF)
- `ros2 bag play --clock` for the selected bag
- RViz2 or Foxglove for visualisation

### 7. Compute localisation error (optional)

While the bag is playing, run in a separate terminal to compute the 2D error between the ground-truth and estimated pose in real time:

```bash
ros2 run turtlebot_datasets calculate_error.py \
    --ros-args -p use_sim_time:=true

# Override frames if needed (defaults: gt=mocap_laser_link, est=base_scan)
ros2 run turtlebot_datasets calculate_error.py \
    --ros-args -p use_sim_time:=true -p gt_frame:=mocap_laser_link -p est_frame:=base_scan
```

### 8. Launch a map server and/or other algorithms

Uncomment the relevant blocks in [turtlebot_playbag.launch.py](launch/turtlebot_playbag.launch.py) to add:
- `nav2_map_server` for a static map
- `nav2_amcl` for Monte-Carlo localisation
- `robot_localization` (EKF) for odometry fusion

---

## Fixing stamp offsets (advanced)

The `fixed_slam_easy` bag distributed with this package has already had its timestamps corrected. The [fix_stamps.py](scripts/fix_stamps.py) script is provided for reference only, in case you need to apply the same correction to a different bag:

```bash
python3 scripts/fix_stamps.py 3961.461462163 slam_easy fixed_slam_easy
```

Arguments: `TIME_OFFSET_SECONDS  INPUT_BAG_DIR  OUTPUT_BAG_DIR`

The script reads every message from `INPUT_BAG_DIR` (a rosbag2 directory), subtracts `TIME_OFFSET` from `/tf` transforms whose parent frame is `mocap`, and writes the corrected bag to `OUTPUT_BAG_DIR`.
