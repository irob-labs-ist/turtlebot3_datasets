cmake_minimum_required(VERSION 3.5)
project(turtlebot3_datasets)

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install scripts
install(PROGRAMS
  scripts/fix_stamps.py
  scripts/download_dataset.sh
  scripts/calculate_error.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

# Install data and config files
install(DIRECTORY
  data
  config
  docs
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
