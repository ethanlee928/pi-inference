# Examples of how to use `pi-utils`

## Input Streams

|                              | Protocol  | Resource URI                    | Notes                                                   |
| ---------------------------- | --------- | ------------------------------- | ------------------------------------------------------- |
| [V4L2 camera](#v4l2-cameras) | `v4l2://` | `v4l2:///dev/video0`            | V4L2 device 0 (substitute other camera numbers for `0`) |
| [Video file](#video-files)   | `file://` | `file://my_video.mp4`           | Supports loading MP4, MKV, AVI (see codecs below)       |
| [RTSP stream](#rtsp)         | `rtsp://` | `rtsp://<ip>:<port>/<endpoint>` | Supports h264, h265 decoding                            |

## Output Streams

|                                  | Protocol     | Resource URI              | Notes                                            |
| -------------------------------- | ------------ | ------------------------- | ------------------------------------------------ |
| [RTSP stream](#rtsp)             | `rtsp://`    | `rtsp://@:1234/my_output` | Reachable at `rtsp://<ip>:1234/my_output`        |
| [TCP stream](#tcp)               | `rtsp://`    | `rtsp://@:1234/my_output` | Reachable at `rtsp://<ip>:1234/my_output`        |
| [Video file](#video-files)       | `file://`    | `file://my_video.mp4`     | Supports saving MP4, MKV, AVI (see codecs below) |
| [OpenGL window](#output-streams) | `display://` | `display://0`             | Creates GUI window on screen 0                   |

## V4L2 Cameras

USB Webcams (tested with Logitech `Brio100`, `C270`)

```bash
python3 video-viewer.py /dev/video0 display://0
```

## Video Files

```bash
python3 video-viewer.py file://path/to/video display://0 --width 1280 --height 720 --framerate 30
```

**[Transcoding Remarks](#transcoding)**

## RTSP

```bash
python3 video-viewer.py rtsp://<ip>:<port>/<endpoint> display://0 --width 1280 --height 720 --framerate 30
```

**[Transcoding Remarks](#transcoding)**

## TCP

## Improvements To Do

### 1. Writable Buffer

- Now every frame is copied from the buffer in `appsink` because the buffer is not writable
- Currently the Python Gst library haven't supported make buffer writable [(Gst.Buffer API)](https://lazka.github.io/pgi-docs/Gst-1.0/classes/Buffer.html)
- [Workaround by jackersson](https://github.com/jackersson/gst-python-hacks/blob/master/how_to_make_gst_buffer_writable.ipynb)

## Remarks

### Transcoding

RPI5 does not support HW decoding and encoding of H.264 and encoding of H.265. However, the format is unsupported by Gstreamer. [Refer to this issue](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/issues/3157)
