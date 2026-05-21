# turtlebot3_datasets --> version ROS2

This package provides helper scripts to download and use datasets for the **Introduction to Robotics** labs.

The datasets were captured on a [Turtlebot 3 Waffle Pi](http://www.robotis.us/turtlebot-3-waffle-pi/).

## Dataset information

A map and rosbag are provided along with some helper scripts.

The initial bag is still provided, but had a synchronization issue. This has been fixed using [fix_stamps.py](scripts/fix_stamps.py).

The fixed bag includes:

```bash
rosbag info fixed_slam_easy.bag

topics:      /imu                              14805 msgs    : sensor_msgs/Imu            
             /odom                              3252 msgs    : nav_msgs/Odometry          
             /raspicam_node/camera_info         1814 msgs    : sensor_msgs/CameraInfo     
             /raspicam_node/image/compressed    1811 msgs    : sensor_msgs/CompressedImage
             /scan                               626 msgs    : sensor_msgs/LaserScan      
             /tf                               21329 msgs    : tf/tfMessage               
             /tf_static                            1 msg     : tf/tfMessage
```

The setup includes ground-truth data. This was obtained from a [motion capture system](http://welcome.isr.tecnico.ulisboa.pt/isrobonet/) at 60Hz. Five markers were placed on the top layer of the robot, such that the center of the tracked object matched the laser scanner of the robot.

The ground-truth data is provided in the `/tf` topic, as a transform `mocap -> mocap_laser_link`. To conform to [REP 105](http://www.ros.org/reps/rep-0105.html) in ROS, the initial transform was obtained at the robot's base footprint frame. The homogeneous transformation matrix at the beginning of the dataset is given by:

![transform](docs/gt_transform.svg)

The initial transform can be used to connect `mocap` to `odom`, `map` or other fixed frames. This can be done by executing [publish_initial_tf.sh](scripts/publish_initial_tf.sh).

Images `docs/unconnected_tree.svg` and `docs/connected_tree.svg` show the setup in terms of frames, and what happens when we add the `mocap -> odom` transform. These images have been obtained with the following bash command: `rosrun tf2_tools view_frames.py`.

The map was obtained using [turtlebot3\_slam](http://wiki.ros.org/turtlebot3_slam) gmapping using the default parameters.

## Notices

First, some things to know:

- Use simulation time when reading data from rosbags. If not, then things like `rospy.Time.now()` will not output the time at which the dataset was recorded. To use simulation time:
    `rosparam set use_sim_time true` after `roscore`. If you were running `rviz` already, it needs to be restarted. Otherwise, TFs might not be picked up.

- Always play back the rosbag with the `--clock` option (related to simulation time). `--pause` and `--r RATE` can also help.

- Check for more information on the [rosbag](http://wiki.ros.org/rosbag/Commandline) command-line tool if necessary.


## Steps

1. Install pip
    `sudo apt get python-pip`
    `sudo pip install --upgrade pip`

2. Install gdown
    `sudo pip install gdown`

3. `git clone https://github.com/irob-labs-ist/turtlebot3_datasets.git` into the **src** directory of your ROS workspace

4. Build with catkin:
    `cd $ROS_WORKSPACE/../src && catkin_make && source ~/.bashrc`

5. Download the dataset (the map is already in the `data` directory, this downloads the rosbag):
    `roscd turtlebot3_datasets/scripts && bash download_dataset.sh`

6. Run a static transform publisher to connect the ground-truth and robot frames (you can also add as a node to [turtlebot3_playbag.launch](launch/turtlebot3_playbag.launch)):
    `rosrun turtlebot3_datasets publish_initial_tf.sh odom # other frames can be used`

7. Launch [turtlebot3_playbag.launch](launch/turtlebot3_playbag.launch) to play the bag:
    `roslaunch turtlebot3_datasets turtlebot3_playbag.launch`

8. Launch map server and/or other algorithms...
