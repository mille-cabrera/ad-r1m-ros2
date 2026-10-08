.. _jetson-index:

NVIDIA\ |reg| Jetson\ |tm| AGX Orin and NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM Integration
=============================================================================================

This section covers integration of the AD-R1M robot with NVIDIA Jetson AGX Orin
and Isaac\ |tm| ROS Visual SLAM for advanced localization and mapping capabilities.

Overview
--------

The NVIDIA Jetson AGX Orin integration extends the AD-R1M platform with GPU-accelerated
visual SLAM capabilities using Isaac ROS Visual SLAM. This enables:

- Real-time visual-inertial odometry
- GPU-accelerated point cloud processing
- Enhanced localization accuracy
- Integration with Nav2 navigation stack

Requirements
------------

- NVIDIA\ |reg| Jetson\ |tm| AGX Orin Developer Kit
- NVIDIA\ |reg| JetPack\ |tm| 7.2 (Ubuntu 24.04), with Docker and the NVIDIA container runtime
- NVIDIA\ |reg| Isaac\ |tm| ROS 4.6 (ROS 2 Jazzy), run inside Docker using the scripts in
  ``ad_r1m_perception_cuvslam/docker``. No ROS, CUDA or Isaac ROS packages are installed on the host.
- Intel\ |reg| RealSense\ |tm| D455 or D435i/D435if camera, firmware 5.16.0.1
- AD-R1M Robot Platform with the AGX Orin as the robot computer, running the robot stack from the ROS 2 Jazzy image (``ad-r1m:robot-jazzy``)

Getting Started
---------------

Follow the setup guides in order:

.. toctree::
   :titlesonly:

   agx-orin-setup
   setup-req-pkg-agx-orin
   setup-isaac-ros-agx-orin
   setup-isaac-ros-vslam
   vslam-setup-and-usage
   ad-r1m-jetson-orin-hardware-setup
   ad-r1m-cuvslam-setup
   ad-r1m-and-nvidia-cuvslam
   map-building-for-nav2
   ad-r1m-realsense-gazebo

