7) AD-R1M and NVIDIA\ |reg| Isaac\ |tm| ROS Visual SLAM setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Docker image built in the previous steps already contains everything needed to run Isaac\ |tm| ROS Visual SLAM
on the AD-R1M platform: ``rmw_zenoh_cpp`` and mDNS (Avahi) to communicate with the robot (ad-r1m-0), and the
startup scripts from ``ad_r1m_perception_cuvslam/docker/entrypoint_additions``.
The remaining steps configure the network link between the AGX Orin and the robot.

.. note::
    The robot and the AGX Orin must run the same ROS 2 distribution (ROS 2 Jazzy, robot image ``ad-r1m:robot-jazzy``).
    Communication between different ROS 2 distributions is not supported.

Network Configuration
^^^^^^^^^^^^^^^^^^^^^

The AGX Orin and the AD-R1M Raspberry Pi communicate using Zenoh as the ROS 2
middleware. Connectivity can be established either wirelessly (if both the RPi and
Jetson are on the same WLAN) or via a direct Ethernet cable for a more reliable,
low-latency link.

The Zenoh settings used by the container are in ``ad_r1m_perception_cuvslam/docker/zenoh.env``.

**Wireless (WLAN)**

If both devices are connected to the same wireless network, no additional network
configuration is needed. Zenoh can discover the robot using mDNS. Set in ``zenoh.env``:

.. code-block:: bash

    RMW_IMPLEMENTATION=rmw_zenoh_cpp
    ZENOH_CONFIG_OVERRIDE=connect/endpoints=["tcp/ad-r1m-0.local:7447"];mode="client"

.. note::

    Wireless connectivity is convenient for development but may introduce higher
    latency and packet loss compared to a wired connection.

**Wired (Ethernet)**

For a more reliable connection, connect the AGX Orin directly to the Raspberry Pi
using an Ethernet cable. Both devices must be configured with static IP addresses
on the same subnet.

*On the AD-R1M Raspberry Pi:*

Create a static Ethernet profile using NetworkManager:

.. code-block:: bash

    sudo nmcli connection add type ethernet con-name eth-static ifname eth0 \
      ipv4.method manual ipv4.addresses 192.168.71.1/24
    sudo nmcli connection up eth-static

Verify the configuration:

.. code-block:: bash

    ip addr show eth0

The output should show ``inet 192.168.71.1/24`` on the ``eth0`` interface.

.. note::

    If ``systemd-networkd`` is also managing ``eth0``, it may conflict with
    NetworkManager. Either disable systemd-networkd for eth0, or configure the
    static IP through systemd-networkd instead by editing
    ``/etc/systemd/network/10-eth0.network``:

    .. code-block:: ini

        [Match]
        Name=eth0

        [Network]
        Address=192.168.71.1/24

    Then run ``sudo networkctl reconfigure eth0``.

*On the AGX Orin:*

Create a static Ethernet profile using NetworkManager:

.. code-block:: bash

    sudo nmcli connection add type ethernet con-name eth-rpi ifname eth0 \
      ipv4.method manual ipv4.addresses 192.168.71.2/24
    sudo nmcli connection up eth-rpi

.. note::

    The Ethernet interface name may vary depending on the platform (e.g. ``eth0``,
    ``eno1``). Run ``nmcli device status`` to identify the correct interface name.

Verify connectivity by pinging from the AGX Orin:

.. code-block:: bash

    ping 192.168.71.1

When using Ethernet, use the RPi's static IP address in ``zenoh.env`` instead of the
mDNS hostname, so that traffic flows over the wired link:

.. code-block:: bash

    RMW_IMPLEMENTATION=rmw_zenoh_cpp
    ZENOH_CONFIG_OVERRIDE=connect/endpoints=["tcp/192.168.71.1:7447"];mode="client"

.. note::

    Using the mDNS hostname (``ad-r1m-X.local``) with a wired connection may cause
    Zenoh to resolve to the RPi's wireless address instead of the Ethernet address,
    routing traffic over WiFi. Using the static IP directly guarantees the wired path.

Start the container
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    cd $ISAAC_ROS_WS/src/ad-r1m-ros2/ad_r1m_perception_cuvslam/docker
    ./run.sh

``run.sh`` loads ``zenoh.env`` each time the container starts. After editing ``zenoh.env``, exit and
restart the container. Rebuilding the image is not needed.

With the robot bringup running, verify that the robot topics are visible from inside the container:

.. code-block:: bash

    ros2 topic list
