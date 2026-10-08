5) NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM and Intel\ |reg| RealSense\ |tm| setup and usage on NVIDIA Jetson\ |tm| AGX Orin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Connect the camera to a USB 3 port on the AGX Orin (USB-A 3.2 ports are recommended).

5.1) Intel RealSense cameras
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Check how the camera is detected (on the host)**

List only the USB devices with VID **0x8086** (Intel):

.. code-block:: bash

    lsusb -d 8086:

The output should be similar to:

.. code-block:: bash

    Bus 002 Device 005: ID 8086:0b3a Intel Corp. Intel(R) RealSense(TM) Depth Camera 435i

**0x0B3A** is the PID of the RealSense D435i. The D435if reports the same PID. The D455 reports **0x0B5C**.

**Install the udev rules (on the host)**

With the camera unplugged:

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    sudo cp 99-realsense-libusb.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger

.. note::
    This is the only RealSense step on the host. The RealSense SDK (v2.56.3) and the ROS wrapper
    (realsense-ros r/4.56.3) are installed inside the Docker image.

**Check the camera inside the container**

Plug in the camera, then start the container:

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh

Inside the container:

.. code-block:: bash

    rs-enumerate-devices -s

Check that the camera is connected over USB 3.x and that the firmware version is **5.16.0.1**,
the version required by Isaac\ |tm| ROS 4.6.

.. warning::
    Updating the firmware with ``rs-fw-update`` writes to the camera flash memory. Do not unplug the camera
    during the update.

**Test with RealSense Viewer (optional)**

On the host, allow the container to open windows on the display:

.. code-block:: bash

    xhost +local:

Inside the container:

.. code-block:: bash

    realsense-viewer

.. figure:: figures/RealSense_viewer_docker.png
    :alt: RealSense viewer inside Docker
    :align: center
    :width: 600px

Select the 2D view mode and enable the Motion Module. Rotate the camera module and check how gyroscope and accelerometer values change.

.. figure:: figures/RealSense_viewer_docker_2D.png
    :alt: RealSense accelerometer and gyroscope in realsense-viewer
    :align: center
    :width: 600px

5.2) Test Isaac ROS Visual SLAM with the RealSense camera
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inside the container, start NVIDIA's RealSense example (stereo + IMU):

.. code-block:: bash

    ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam_realsense.launch.py

.. note::
    This NVIDIA example uses ``accel_fps: 200``. For the D435i/D435if, NVIDIA recommends 250.
    The AD-R1M configuration (**vslam_single_realsense.yaml**) already uses 250.

Open a second terminal on the host and attach to the running container:

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh

Check the topics and their rates:

.. code-block:: bash

    ros2 topic list
    ros2 topic hz /camera/infra1/image_rect_raw
    ros2 topic hz /camera/imu
    ros2 topic hz /visual_slam/tracking/odometry

The odometry rate should match the camera frame rate. The topic list should include:

.. code-block:: bash

    /camera/imu
    /camera/infra1/camera_info
    /camera/infra1/image_rect_raw
    /camera/infra2/camera_info
    /camera/infra2/image_rect_raw
    /tf
    /tf_static
    /visual_slam/status
    /visual_slam/tracking/odometry
    /visual_slam/tracking/slam_path
    /visual_slam/tracking/vo_path
    /visual_slam/tracking/vo_pose
    /visual_slam/tracking/vo_pose_covariance
    /visual_slam/vis/landmarks_cloud
    /visual_slam/vis/observations_cloud

**Visualize in RViz**

If ``rviz2`` is not available in the container, install it (it is removed when the container exits;
add ``ros-jazzy-rviz2`` to ``Dockerfile.ad_r1m_cuvslam`` to keep it):

.. code-block:: bash

    sudo apt-get update && sudo apt-get install -y ros-jazzy-rviz2

.. code-block:: bash

    rviz2 -d $(ros2 pkg prefix isaac_ros_visual_slam --share)/rviz/realsense.cfg.rviz

.. figure:: figures/RViz2_pointcloud_docker.png
    :alt: Isaac ROS Visual SLAM demo run
    :align: center
    :width: 600px

**Reference links**

This tutorial is based on the official **NVIDIA Isaac ROS 4.6** documentation:
    * https://nvidia-isaac-ros.github.io/v/release-4.6/repositories_and_packages/isaac_ros_visual_slam/isaac_ros_visual_slam/index.html
    * https://nvidia-isaac-ros.github.io/v/release-4.6/concepts/visual_slam/cuvslam/tutorial_realsense.html
    * https://nvidia-isaac-ros.github.io/v/release-4.6/getting_started/sensors/realsense_setup.html