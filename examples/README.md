# Examples of how to use `pi-utils`

## Input Streams

|                              | Protocol  | Resource URI          | Notes                                                   |
| ---------------------------- | --------- | --------------------- | ------------------------------------------------------- |
| [V4L2 camera](#v4l2-cameras) | `v4l2://` | `v4l2:///dev/video0`  | V4L2 device 0 (substitute other camera numbers for `0`) |
| [Video file](#video-files)   | `file://` | `file://my_video.mp4` | Supports loading MP4, MKV, AVI (see codecs below)       |

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

## RTSP

## TCP
