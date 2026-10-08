
# `ad_r1m_perception_cuvslam` ROS2 Package

This package provides the launch files and URDF descriptions needed to start and use the base navigation functionality of the AD_R1M platform together with NVIDIA® Isaac™ ROS Visual SLAM.  
Note: This is a *high‑level overview*. Full setup instructions and detailed documentation are available on the [official AD-R1M documentation page](https://developer.analog.com/docs/system-level/solutions/reference-designs/ad-r1m/index.html#getting-started).

## Prerequisites

### Hardware
- AD_R1M mobile robot platform
- NVIDIA® Jetson™ AGX Orin or any desktop station with an NVIDIA GPU  
  (setup instructions are provided only for the AGX Orin variant)
- Intel® RealSense™ camera(s)  
  (ZED cameras are also supported by NVIDIA Isaac ROS, but they are not part of our standard hardware setup. For ZED configuration details, see: https://nvidia-isaac-ros.github.io/getting_started/sensors/zed_setup.html)

### Software
- NVIDIA® JetPack™ 7.2 (Ubuntu 24.04) on the AGX Orin, with Docker and the NVIDIA container runtime
- NVIDIA Isaac ROS **4.6** (ROS 2 **Jazzy**), provided inside a Docker image built from [`docker/`](docker/).
  Nothing ROS-, CUDA- or Isaac-related is installed on the Jetson host.
- Intel RealSense SDK v2.56.3 and realsense-ros r/4.56.3 (built into the image). Camera firmware must be **5.16.0.1**.

### Simulation
- Gazebo Ignition  
  A Gazebo model of AD‑R1M equipped with a Intel RealSense D435i is provided for testing AD‑R1M + Isaac ROS Visual SLAM functionality in simulation.

All setup steps and requirements related to AD‑R1M and NVIDIA Isaac ROS Visual SLAM can be found on the official documentation page.

## Docker Environment (AGX Orin)

The container is built and started with the scripts in [`docker/`](docker/):

| File | Purpose |
|---|---|
| `docker/build.sh` | Clones NVIDIA `isaac-ros-cli` (`release-4.6`) into `~/.cache/ad_r1m/` (not installed) and builds the image layers: Isaac ROS base → RealSense → `Dockerfile.ad_r1m_cuvslam` |
| `docker/Dockerfile.ad_r1m_cuvslam` | Adds Isaac ROS Visual SLAM, `rmw_zenoh_cpp` and mDNS/Avahi on top of the NVIDIA layers |
| `docker/run.sh` | Starts the container (or opens a new shell in it if it is already running) |
| `docker/zenoh.env` | Zenoh settings used to reach the robot (`RMW_IMPLEMENTATION`, `ZENOH_CONFIG_OVERRIDE`) |
| `docker/entrypoint_additions/` | Scripts run at container start (Avahi + D-Bus for mDNS) |

### One-time host setup

Only system configuration is needed on the Jetson host:

- Check that Docker, the NVIDIA runtime and `buildx` are available:

```bash
    docker buildx version
    docker run --rm --gpus all ubuntu:24.04 true
```

- Install the RealSense udev rules (with the camera unplugged):

```bash
    wget https://raw.githubusercontent.com/realsenseai/librealsense/v2.56.3/config/99-realsense-libusb.rules
    sudo mv 99-realsense-libusb.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger
```

- Set the robot address in `docker/zenoh.env` (wired Ethernet: `tcp/192.168.71.1:7447`, WLAN: `tcp/ad-r1m-0.local:7447`).

### Build and start the container

```bash
    export ISAAC_ROS_WS=~/workspaces/isaac_ros-dev
    mkdir -p $ISAAC_ROS_WS/src && cd $ISAAC_ROS_WS/src
    git clone https://github.com/analogdevicesinc/ad-r1m-ros2

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./build.sh    # first time only, takes a while
    ./run.sh
```

Inside the container, build this package (only this package: the other packages in the repository run on the robot):

```bash
    colcon build --symlink-install --packages-select ad_r1m_perception_cuvslam
    source install/setup.bash
```

Verify the camera is detected over USB 3 with firmware 5.16.0.1:

```bash
    rs-enumerate-devices -s
```

> The container is started with `--rm`. Keep anything you want to persist, such as cuVSLAM maps, under `/workspaces/isaac_ros-dev`.

## Use Cases

### 1) Real Robot

After completing all setup steps from the official documentation:

- Calibrate the extrinsic parameters of your RealSense camera (depending on how it is mounted on the robot) using the file:  
  **urdf/single_realsense_calibration.urdf.xacro**

  Despite the file name, you may configure multiple RealSense cameras as long as you provide the appropriate static transforms.

```r
    <robot name="adrd_demo_ros2">
      <link name="ad_r1m_0/base_link" />

      <joint name="camera1" type="fixed">
        <parent link="ad_r1m_0/base_link"/>
        <child link="camera1_link"/>
        <origin xyz="0.335 0.0 0.0" rpy="0 0 0"/>
      </joint>
      ...
    </robot>
```

  The default values correspond to a camera mounted in front of the robot, above the ToF camera (0.335 m translation on the X-axis and zero rotation on all axes).

- Set the `serial_no` of your camera in **config/vslam_single_realsense.yaml** (get it with `rs-enumerate-devices -s`).

- On your NVIDIA® Jetson™ AGX Orin, start the container (see [Docker Environment](#docker-environment-agx-orin)):

```bash
    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh
```

- Inside the container, for a single RealSense camera:

```bash
    source install/setup.bash
    P=$(ros2 pkg prefix ad_r1m_perception_cuvslam)/share/ad_r1m_perception_cuvslam
    ros2 launch ad_r1m_perception_cuvslam cuvslam_multirealsense.launch.py \
        config_path:=$P/config/vslam_single_realsense.yaml \
        urdf_file:=$P/urdf/single_realsense_calibration.urdf.xacro
```

  Without arguments, the launch file uses the multi-camera configuration (**config/vslam_multi_realsense.yaml**, **urdf/realsense_calibration.urdf.xacro**).

This starts all required RealSense and Isaac ROS Visual SLAM nodes.

### 2) Simulation

- Connect the host computer (running Gazebo) to the AGX Orin via Ethernet.

- Launch the simulation on the host:

```r
    ros2 launch ad_r1m_perception_cuvslam robot_realsense_sim.launch.py \
        local_models_path:=<path_to_your_models> \
        world_name:=<your_world_name.world>
```

- On the NVIDIA Jetson AGX Orin, start the container:

```bash
    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh
```

- Inside the container:

```bash
    source install/setup.bash
    ros2 launch ad_r1m_perception_cuvslam vslam_single_realsense.launch.py
```

## Configuration
Configuration files for RealSense cameras and Isaac ROS Visual SLAM parameters can be found in **config/**. 
- Real robot, single camera: *vslam_single_realsense.yaml* (`tracking_mode: 1`, stereo + IMU)
- Real robot, multiple cameras: *vslam_multi_realsense.yaml* (`tracking_mode: 0`, stereo only)
- Simulation: *cuvslam_single_realsense.yaml* (`tracking_mode: 0`)

`tracking_mode` is set under the `visual_slam:` section: `0` = stereo (one or more stereo cameras), `1` = stereo + IMU (VIO), `2` = RGB-D. It replaces the former `enable_imu_fusion` parameter.

More details on how to configure Isaac ROS Visual SLAM or RealSense parameters can be found at their official documentation pages (Isaac ROS 4.6):
- https://nvidia-isaac-ros.github.io/v/release-4.6/repositories_and_packages/isaac_ros_visual_slam/isaac_ros_visual_slam/index.html
- https://nvidia-isaac-ros.github.io/v/release-4.6/concepts/visual_slam/cuvslam/tutorial_realsense.html
- https://nvidia-isaac-ros.github.io/v/release-4.6/getting_started/sensors/realsense_setup.html
- https://github.com/realsenseai/realsense-ros