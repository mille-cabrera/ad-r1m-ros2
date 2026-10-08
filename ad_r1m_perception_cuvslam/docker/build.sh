#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
CLI_DIR=${CLI_DIR:-$HOME/.cache/ad_r1m/isaac-ros-cli-4.6}
[ -d "$CLI_DIR" ] || git clone --depth 1 -b release-4.6 https://github.com/NVIDIA-ISAAC-ROS/isaac-ros-cli.git "$CLI_DIR"
ARGS=(--build-arg PLATFORM=arm64 --build-arg ISAAC_ROS_PLATFORM=arm64-jetpack --build-arg ISAAC_DEBIAN_DISTRO_SUFFIX=-jetpack)
docker buildx build --load "${ARGS[@]}" -f "$CLI_DIR/docker/Dockerfile.isaac_ros" -t ad_r1m/isaac_ros_base:4.6 "$CLI_DIR"
docker buildx build --load "${ARGS[@]}" --build-arg BASE_IMAGE=ad_r1m/isaac_ros_base:4.6 \
  -f "$CLI_DIR/docker/Dockerfile.realsense" -t ad_r1m/isaac_ros_realsense:4.6 "$CLI_DIR/docker"
docker buildx build --load --build-arg BASE_IMAGE=ad_r1m/isaac_ros_realsense:4.6 \
  -f "$HERE/Dockerfile.ad_r1m_cuvslam" -t ad_r1m/cuvslam:isaac-ros-4.6 "$HERE"