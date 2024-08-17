import logging
import time
from threading import Thread

import cv2
import gi
import supervision as sv

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst, GstRtspServer

Gst.init(None)

from pi_utils import functions as f
from pi_utils.source import VideoSource
from rtsp_server import launch_rtsp_server

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
FRAMERATE = 10


def create_pipeline():
    pipeline = Gst.Pipeline.new("sink-pipeline")

    # Create elements
    source = f.make_element("appsrc")
    videoconvert = f.make_element("videoconvert")
    encoder = f.make_element("x264enc")
    parser = f.make_element("h264parse")
    rtppay = f.make_element("rtph264pay")
    queue = f.make_element("queue")
    sink = f.make_element("udpsink")

    f.add_elements(pipeline, [source, videoconvert, encoder, parser, rtppay, queue, sink])
    f.link_elements([source, videoconvert, encoder, parser, rtppay, queue, sink])

    # Set properties
    source.set_property("is-live", True)
    source.set_property("block", True)
    source.set_property("format", Gst.Format.TIME)
    source.set_property(
        "caps",
        Gst.Caps.from_string(
            f"video/x-raw,format=BGR,width={FRAME_WIDTH},height={FRAME_HEIGHT},framerate={FRAMERATE}/1"
        ),
    )
    sink.set_property("host", "0.0.0.0")
    sink.set_property("port", 5000)
    sink.set_property("async", False)
    rtppay.set_property("pt", 96)

    return pipeline, source


def create_pipeline_v2():
    pipeline = Gst.Pipeline.new("sink-pipeline")

    # Create elements
    source = f.make_element("appsrc")
    videoconvert = f.make_element("videoconvert")
    queue = f.make_element("queue")
    sink = f.make_element("autovideosink")

    f.add_elements(pipeline, [source, videoconvert, queue, sink])
    f.link_elements([source, videoconvert, queue, sink])

    # Set properties
    source.set_property("do-timestamp", True)
    source.set_property("is-live", True)
    source.set_property("block", True)
    source.set_property("format", Gst.Format.TIME)
    source.set_property(
        "caps",
        Gst.Caps.from_string(
            f"video/x-raw,format=BGR,width={FRAME_WIDTH},height={FRAME_HEIGHT},framerate={FRAMERATE}/1"
        ),
    )
    return pipeline, source


def rtsp_server_loop():
    print("Launching RTSP Server")
    launch_rtsp_server()
    loop = GLib.MainLoop()
    loop.run()
    print("Exit RTSP Server MainLoop ...")


if __name__ == "__main__":
    idx = 0
    last_update = time.time()
    fps_monitor = sv.FPSMonitor()

    sink_pipeline, appsrc = create_pipeline()
    sink_pipeline.set_state(Gst.State.PLAYING)
    video_source = VideoSource(
        "/dev/video0", width=FRAME_WIDTH, height=FRAME_HEIGHT, codec="mjpeg", framerate=FRAMERATE
    )

    print("Starting RTSP Server thread")
    Thread(target=rtsp_server_loop, daemon=True).start()
    print("Starting RTSP Server thread DONE")

    while True:
        try:
            frame = video_source.capture(timeout=300)
            now = time.time()
            if frame is not None:
                fps_monitor.tick()
                buffer = Gst.Buffer.new_wrapped(frame.tobytes())
                buffer.pts = appsrc.get_current_running_time()
                buffer.dts = Gst.CLOCK_TIME_NONE
                buffer.duration = Gst.CLOCK_TIME_NONE
                result = appsrc.emit("push-buffer", buffer)
                if result != Gst.FlowReturn.OK:
                    print(f"Failed to push buffer: {result}")

                if now - last_update > 1:
                    last_update = now
                    logging.info("FPS: %.1f", fps_monitor.fps)
                    logging.info("Frame Shape: %s", frame.shape)
        except KeyboardInterrupt:
            break

    video_source.on_terminate()
    sink_pipeline.set_state(Gst.State.NULL)
