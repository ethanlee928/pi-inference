# Examples of how to use `pi-inference`

## Input Streams

|                              | Protocol  | Resource URI                    | Notes                                                   |
| ---------------------------- | --------- | ------------------------------- | ------------------------------------------------------- |
| [V4L2 camera](#v4l2-cameras) | `v4l2://` | `v4l2:///dev/video0`            | V4L2 device 0 (substitute other camera numbers for `0`) |
| [CSI Camera](#csi-cameras)   | `csi://`  | `csi://<device-name>`           | Based on `libcamerasrc`                                 |
| [Video file](#video-files)   | `file://` | `file://my_video.mp4`           | Supports loading MP4, MKV, AVI (see codecs below)       |
| [RTSP stream](#rtsp)         | `rtsp://` | `rtsp://<ip>:<port>/<endpoint>` | Supports h264, h265 decoding                            |

## Output Streams

|                                  | Protocol     | Resource URI              | Notes                                            |
| -------------------------------- | ------------ | ------------------------- | ------------------------------------------------ |
| [RTSP stream](#rtsp)             | `rtsp://`    | `rtsp://@:1234/my_output` | Reachable at `rtsp://<ip>:1234/my_output`        |
| [TCP stream](#tcp)               | `tcp://`     | `tcp://0.0.0.0:5000`      | Reachable at `tcp://<ip>:5000`                   |
| [Video file](#video-files)       | `file://`    | `file://my_video.mp4`     | Supports saving MP4, MKV, AVI (see codecs below) |
| [OpenGL window](#output-streams) | `display://` | `display://0`             | Creates GUI window on screen 0                   |

## V4L2 Cameras

USB Webcams (tested with Logitech `Brio100`, `C270`)

```bash
python3 video-viewer.py v4l2:///dev/video0 display://0
```

## CSI Cameras

Check CSI Cameras

```bash
# Check camera name
rpicam-hello --list
# Example output
Available cameras
-----------------
0 : imx708_noir [4608x2592 10-bit RGGB] (/base/axi/pcie@120000/rp1/i2c@88000/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [120.13 fps - (768, 432)/3072x1728 crop]
                             2304x1296 [56.03 fps - (0, 0)/4608x2592 crop]
                             4608x2592 [14.35 fps - (0, 0)/4608x2592 crop]
```

CSI Camera to OpenGL Window (tested with Pi Camera Module 3 NoIR)

```bash
python3 video-viewer.py csi:///base/axi/pcie@120000/rp1/i2c@88000/imx708@1a display://0
```

## Video Files

Video file to OpenGL Window

```bash
python3 video-viewer.py file://path/to/video display://0 --width 1280 --height 720 --framerate 30
```

**[Transcoding Remarks](#transcoding)**

## RTSP

RTSP Stream to OpenGL Window

```bash
python3 video-viewer.py rtsp://<ip>:<port>/<endpoint> display://0 --width 1280 --height 720 --framerate 30
```

USB Camera to RTSP Stream

```bash
python3 video-viewer.py v4l2:///dev/video0 rtsp://<ip>:<port>/<endpoint> --width 1280 --height 720 --framerate 30
```

## TCP

USB Camera to TCP Stream

```bash
python3 video-viewer.py v4l2:///dev/video0 rtsp://<ip>:<port>/<endpoint> --width 1280 --height 720 --framerate 30
```

**[Transcoding Remarks](#transcoding)**

## Improvements To Do

### 1. Writable Buffer

- Now every frame is copied from the buffer in `appsink` because the buffer is not writable
- Currently the Python Gst library haven't supported make buffer writable [(Gst.Buffer API)](https://lazka.github.io/pgi-docs/Gst-1.0/classes/Buffer.html)
- [Workaround by jackersson](https://github.com/jackersson/gst-python-hacks/blob/master/how_to_make_gst_buffer_writable.ipynb)

## Remarks

### Transcoding

RPI5 does not support HW decoding and encoding of H.264 and encoding of H.265. However, the format is unsupported by Gstreamer. [Refer to this issue](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/issues/3157)
