# ad_r1m_perception_realsense

Uses an Intel RealSense **D435i / D435if** as the AD-R1M 2D scan source for SLAM Toolbox and Nav2,
without cuVSLAM / Isaac ROS:

```
realsense2_camera (depth only, 848x480@30)
  /camera/camera/depth/image_rect_raw (16UC1, mm) + /camera/camera/depth/camera_info
        |
depthimage_to_laserscan (repo fork, scan_offset)  -> /scan  (frame camera_depth_frame)
        |
slam_toolbox / Nav2 (unchanged, scan_topic: scan)
```

## Launch files

| File | What it starts |
|---|---|
| `launch/realsense.launch.py` | `realsense2_camera_node` + static TF `base_link -> camera_link` (mount pose) |
| `launch/realsense_scan.launch.py` | The above + `depthimage_to_laserscan` -> `/scan` (`use_camera:=false` to convert a bag) |

On the Jetson, use the switchable bringup in `ad_r1m_jetson` instead:

```bash
ros2 launch ad_r1m_jetson ad_r1m_nav_bringup.launch.py depth_source:=realsense \
  mount_x:=0.2755 mount_y:=0.0 mount_z:=0.06 mount_pitch:=0.0
```

## TF

| Edge | Publisher |
|---|---|
| `base_link -> camera_link` | `static_transform_publisher` in `realsense.launch.py` (`mount_*` args, `publish_mount_tf`) |
| `camera_link -> camera_depth_frame -> camera_depth_optical_frame` | `realsense2_camera` (`publish_tf: true`, factory extrinsics) |

`camera_link` is the left IR imager (depth origin), not the centre of the camera body.
The default mount (x 0.2755, z 0.06, level) is the ToF mount of `ad_r1m_base.urdf.xacro`;
measure the real mount and override it. `depthimage_to_laserscan` assumes a roughly level camera;
if the camera is pitched down, raise `scan_offset` / limit `range_max`, or switch to
`pointcloud_to_laserscan` with `target_frame: base_link` and `min_height`/`max_height`.

## Configuration

- `config/realsense_d435if.yaml`: depth only, `848,480,30`, `initial_reset: true`, filters off.
  The D435if has an IR-pass filter, so depth relies on the IR projector: keep the emitter on
  (device default). Do not reuse the cuVSLAM configs, which set `depth_module.emitter_enabled: 0`.
- `config/depth_to_laser_realsense.yaml`: `range_min 0.3`, `range_max 4.0`, `scan_height 20`,
  `scan_offset 0.5`.

## Prerequisites

- Packages `ros-${ROS_DISTRO}-realsense2-camera` / `librealsense2` (resolved by rosdep from
  `package.xml`). The D435if enumerates as `Intel RealSense D435I`.
- USB 3 connection; RealSense udev rules on the host; the container needs USB access
  (`--privileged -v /dev:/dev`).

## Verify

```bash
rs-enumerate-devices -s                                   # camera visible, serial, firmware
rs-enumerate-devices | grep -i "usb type"                 # 3.x expected
ros2 topic hz /camera/camera/depth/image_rect_raw         # ~30 Hz
ros2 topic echo --once /scan --field header               # frame_id camera_depth_frame
ros2 run tf2_ros tf2_echo base_link camera_depth_frame    # matches the mount
ros2 param get /camera/camera depth_module.emitter_enabled
```
