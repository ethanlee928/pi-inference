import logging
import time

import supervision as sv

from pi_utils.source import VideoSource

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s: %(message)s")


if __name__ == "__main__":
    idx = 0
    last_update = time.time()
    fps_monitor = sv.FPSMonitor()

    video_source = VideoSource("/dev/video0", width=1920, height=1080, codec="mjpeg", framerate=10)
    while True:
        try:
            frame = video_source.capture(timeout=200)
            now = time.time()
            if frame is not None:
                fps_monitor.tick()
                if now - last_update > 1:
                    last_update = now
                    logging.info("FPS: %.1f", fps_monitor.fps)
                    logging.info("Frame Shape: %s", frame.shape)
        except KeyboardInterrupt:
            break

    video_source.on_terminate()
