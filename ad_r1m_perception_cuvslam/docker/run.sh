#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); WS=${ISAAC_ROS_WS:?set ISAAC_ROS_WS}; NAME=ad_r1m_cuvslam
if [ -n "$(docker ps -q -f name=^${NAME}$)" ]; then exec docker exec -it -u admin -w /workspaces/isaac_ros-dev $NAME bash; fi
exec docker run -it --rm --name $NAME --privileged --network host --ipc=host --pid=host --gpus all \
  -e DISPLAY -e NVIDIA_VISIBLE_DEVICES=all -e NVIDIA_DRIVER_CAPABILITIES=all -e ROS_DOMAIN_ID -e USER \
  -e HOST_USER_UID=$(id -u) -e HOST_USER_GID=$(id -g) -e ISAAC_ROS_WS=/workspaces/isaac_ros-dev \
  --env-file "$HERE/zenoh.env" \
  -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev/bus/usb:/dev/bus/usb -v /dev/input:/dev/input \
  -v /usr/lib/aarch64-linux-gnu/tegra:/usr/lib/aarch64-linux-gnu/tegra -v /usr/share/vpi3:/usr/share/vpi3 \
  -v /usr/bin/tegrastats:/usr/bin/tegrastats -v /sys/kernel/debug:/sys/kernel/debug:ro \
  -v "$WS":/workspaces/isaac_ros-dev -v /etc/localtime:/etc/localtime:ro \
  -w /workspaces/isaac_ros-dev --entrypoint /usr/local/bin/scripts/workspace-entrypoint.sh \
  ad_r1m/cuvslam:isaac-ros-5.0 /bin/bash