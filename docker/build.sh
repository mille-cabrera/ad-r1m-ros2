#!/usr/bin/env bash
#
# Build the ad-r1m image with buildx.
#
# RUN THIS FROM THE <repo>/docker/ DIRECTORY:
#   cd <repo>/docker
#   ./build.sh                # build using cache (default)
#   ./build.sh --cache        # build using cache (explicit)
#   ./build.sh --no-cache     # force a clean rebuild (ignore cache)
#
# Any extra args are passed straight through to `docker buildx build`, e.g.:
#   ./build.sh --no-cache --progress=plain
#   ./build.sh --build-arg ROS_DISTRO=humble
#
# Env overrides:
#   TAG=ad-r1m:dev   ROS_DISTRO=jazzy   TARGET=dev   ./build.sh

set -euo pipefail

# --- paths: context is the repo root (parent of this docker/ dir) -------------
CONTEXT_DIR=".."
DOCKERFILE="Dockerfile"

# Guard: make sure we're actually in the docker/ dir
if [ ! -f "${DOCKERFILE}" ]; then
    echo "ERROR: '${DOCKERFILE}' not found in the current directory." >&2
    echo "       Run this script from inside <repo>/docker/" >&2
    exit 1
fi

# --- configurable defaults (override via env) --------------------------------
TAG="${TAG:-ad-r1m:jetson-jazzy}"
TARGET="${TARGET:-dev}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
BUILD_PACKAGES="${BUILD_PACKAGES:-ad_r1m_robot adi_3dtof_adtf31xx ad_r1m_jetson ad_r1m_teleop_joy}"

# --- parse cache option; collect the rest as pass-through args ----------------
CACHE_ARGS=()
PASSTHROUGH=()
for arg in "$@"; do
    case "$arg" in
        --no-cache)
            CACHE_ARGS=(--no-cache)
            ;;
        --cache)
            CACHE_ARGS=()   # default behaviour: use cache
            ;;
        *)
            PASSTHROUGH+=("$arg")
            ;;
    esac
done

# --- show what we're about to do ---------------------------------------------
echo "Context       : $(cd "${CONTEXT_DIR}" && pwd)"
echo "Dockerfile    : ${DOCKERFILE}"
echo "Target        : ${TARGET}"
echo "Tag           : ${TAG}"
echo "ROS_DISTRO    : ${ROS_DISTRO}"
echo "BUILD_PACKAGES: ${BUILD_PACKAGES}"
echo "Cache         : $([ ${#CACHE_ARGS[@]} -eq 0 ] && echo enabled || echo disabled '(--no-cache)')"
echo

# --- optional GH_TOKEN secret (Dockerfile mounts id=GH_TOKEN for private vcs) -
SECRET_ARGS=()
if [ -n "${GH_TOKEN:-}" ]; then
    SECRET_ARGS=(--secret id=GH_TOKEN,env=GH_TOKEN)
    echo "Using GH_TOKEN from environment for private git sources."
    echo
fi

# --- build -------------------------------------------------------------------
set -x
docker buildx build "${CONTEXT_DIR}" \
    -f "${DOCKERFILE}" \
    --target "${TARGET}" \
    --build-arg ROS_DISTRO="${ROS_DISTRO}" \
    --build-arg BUILD_PACKAGES="${BUILD_PACKAGES}" \
    -t "${TAG}" \
    "${CACHE_ARGS[@]}" \
    "${SECRET_ARGS[@]}" \
    "${PASSTHROUGH[@]}"
