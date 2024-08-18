import logging
import time

import gi
import supervision as sv

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

from pi_utils.sink import VideoOutput
from pi_utils.source import VideoSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAMERATE = 10


if __name__ == "__main__":
    idx = 0
    last_update = time.time()
    fps_monitor = sv.FPSMonitor()

    video_source = VideoSource(
        "/dev/video0",
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        codec="mjpeg",
        framerate=FRAMERATE,
    )
    video_output = VideoOutput(
        "rtsp://@:8554/base",
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        framerate=FRAMERATE,
    )

    while True:
        try:
            frame = video_source.capture(timeout=300)
            now = time.time()
            if frame is not None:
                fps_monitor.tick()
                video_output.render(frame)
                if now - last_update > 1:
                    last_update = now
                    logging.info("FPS: %.1f", fps_monitor.fps)
                    logging.info("Frame Shape: %s", frame.shape)
        except KeyboardInterrupt:
            break

    video_source.on_terminate()
    video_output.on_terminate()
