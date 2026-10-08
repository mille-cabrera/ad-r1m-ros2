7) AD-R1M and NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this setup the NVIDIA\ |reg| Jetson\ |tm| AGX Orin is the robot computer. It runs the whole AD-R1M ROS 2 stack
(IMU, motors, ToF, EKF, Nav2) and Isaac\ |tm| ROS Visual SLAM with the Intel\ |reg| RealSense\ |tm| camera.
No second computer or network link between computers is needed.

Both parts run in Docker containers on the AGX Orin and share the host network:

.. code-block:: text

    Jetson AGX Orin
    ├─ zenoh_router        rmw_zenohd on localhost:7447 (one per machine)
    ├─ robot stack         ad-r1m:robot-jazzy containers (IMU, motors, ToF, EKF, Nav2, ...)
    └─ Isaac ROS VSLAM     ad_r1m/cuvslam:isaac-ros-4.6 container (RealSense + Visual SLAM)

ROS 2 middleware
^^^^^^^^^^^^^^^^

All containers use Zenoh (``rmw_zenoh_cpp``) and communicate through a single Zenoh router running on the AGX Orin.
The router is the ``zenoh_router`` service of the robot stack. Start it before the other components.

The Isaac ROS Visual SLAM container reads its middleware settings from
``ad_r1m_perception_cuvslam/docker/zenoh.env``:

.. code-block:: bash

    RMW_IMPLEMENTATION=rmw_zenoh_cpp

No Zenoh endpoint needs to be configured: by default, ``rmw_zenoh_cpp`` connects to the router on
``tcp/localhost:7447``.

.. important::
    * All containers must use the same ``RMW_IMPLEMENTATION`` and the same ``ROS_DOMAIN_ID``
      (``ROS_DOMAIN_ID`` unset everywhere means domain 0).
    * All containers must run the same ROS 2 distribution (ROS 2 Jazzy).

Frame names
^^^^^^^^^^^

The robot bringup runs in the root namespace, so the robot frames are ``base_link`` and ``odom``.
The Isaac ROS Visual SLAM configuration (**vslam_single_realsense.yaml**) and the camera mounting
(**single_realsense_calibration.urdf.xacro**) use the same names:

.. code-block:: yaml

    visual_slam:
      base_frame: 'base_link'
      odom_frame: 'odom'

If the robot bringup is started with a namespace (e.g. ``ad_r1m_0``), use the prefixed frame names
(``ad_r1m_0/base_link``, ``ad_r1m_0/odom``) in both files.

.. note::
    The camera mounting is published by a separate ``robot_state_publisher`` (``realsense_state_publisher``).
    Its robot description is remapped to ``/realsense_robot_description`` so that it does not replace the
    robot's own ``/robot_description``, which is used by ``ros2_control``.

Start the container
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh

``run.sh`` loads ``zenoh.env`` each time the container starts. After editing ``zenoh.env``, exit and
restart the container. Rebuilding the image is not needed.

With the robot stack running, verify from inside the container that the robot topics and transforms are visible:

.. code-block:: bash

    ros2 topic list
    ros2 run tf2_ros tf2_echo odom base_link