4) Setup NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM runs inside a Docker container based on Isaac\ |tm| ROS 4.6
(ROS 2 Jazzy, JetPack\ |tm| 7.2). The image is built with the scripts in
``ad_r1m_perception_cuvslam/docker``. No ROS, CUDA or Isaac ROS packages are installed on the host.

4.1) Check the host prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Docker, the NVIDIA container runtime and ``buildx`` are provided by JetPack\ |tm|. Verify them:

.. code-block:: bash

    docker buildx version
    docker run --rm --gpus all ubuntu:24.04 true

Add the current user to the docker group:

.. code-block:: bash

    sudo usermod -aG docker $USER && newgrp docker

4.2) Clone the AD-R1M repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    export ISAAC_ROS_WS=~/workspaces/isaac_ros-dev
    mkdir -p $ISAAC_ROS_WS/src && cd $ISAAC_ROS_WS/src
    git clone https://github.com/analogdevicesinc/ad-r1m-ros2

.. tip::
    Add ``export ISAAC_ROS_WS=~/workspaces/isaac_ros-dev`` to ``~/.bashrc`` so it is set in every terminal.

4.3) Build the Docker image
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./build.sh

``build.sh`` clones NVIDIA ``isaac-ros-cli`` (``release-4.6``) into ``~/.cache/ad_r1m/`` (it is not installed)
and builds three image layers:

#. Isaac\ |tm| ROS 4.6 base (ROS 2 Jazzy)
#. Intel\ |reg| RealSense\ |tm| SDK v2.56.3 and realsense-ros r/4.56.3
#. ``Dockerfile.ad_r1m_cuvslam``: Isaac\ |tm| ROS Visual SLAM, ``rmw_zenoh_cpp`` and Avahi (mDNS)

.. note::
    The first build compiles librealsense from source and can take a long time.
    Later starts reuse the image.

4.4) Start the container and build the AD-R1M package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh

Running ``./run.sh`` again from another terminal opens a new shell in the running container.

Inside the container, build only the cuVSLAM package (the other packages in the repository run on the robot):

.. code-block:: bash

    colcon build --symlink-install --packages-select ad_r1m_perception_cuvslam
    source install/setup.bash

.. important::
    The container is started with ``--rm``: everything outside ``/workspaces/isaac_ros-dev`` is lost when it exits.
    Keep maps, bags and logs under ``/workspaces/isaac_ros-dev`` (``$ISAAC_ROS_WS`` on the host).

4.5) (Optional) Download quickstart data from NGC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only needed to run the NVIDIA rosbag quickstart. Run inside the container:

.. code-block:: bash

    sudo apt-get update && sudo apt-get install -y curl jq tar

.. code-block:: bash

    NGC_ORG="nvidia"
    NGC_TEAM="isaac"
    PACKAGE_NAME="isaac_ros_visual_slam"
    NGC_RESOURCE="isaac_ros_visual_slam_assets"
    NGC_FILENAME="quickstart.tar.gz"
    MAJOR_VERSION=4
    MINOR_VERSION=6
    VERSION_REQ_URL="https://api.ngc.nvidia.com/v2/resources/$NGC_ORG/$NGC_TEAM/$NGC_RESOURCE/versions"
    AVAILABLE_VERSIONS=$(curl -s \
        -H "Accept: application/json" "$VERSION_REQ_URL")
    LATEST_VERSION_ID=$(echo $AVAILABLE_VERSIONS | jq -r "
        .recipeVersions[]
        | .versionId as \$v
        | \$v | select(test(\"^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$\"))
        | split(\".\") | {major: .[0]|tonumber, minor: .[1]|tonumber, patch: .[2]|tonumber}
        | select(.major == $MAJOR_VERSION and .minor <= $MINOR_VERSION)
        | \$v
        " | sort -V | tail -n 1
    )
    if [ -z "$LATEST_VERSION_ID" ]; then
        echo "No cor