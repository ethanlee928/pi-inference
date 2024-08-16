import logging
import subprocess
import threading
import time
from typing import Optional

import cv2
import gi
import numpy as np
import supervision as sv

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s %(message)s")

logger = logging.getLogger("GstSource")

# Initialize GStreamer
Gst.init(None)

idx = 0
last_update = time.time()
fps_monitor = sv.FPSMonitor()


def output_pipeline_dot(pipeline, filename: str = "pipeline"):
    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, filename)


def make_element(element_name, name=None):
    _name = element_name if name is None else name
    element = Gst.ElementFactory.make(element_name, _name)
    print(element)
    if element is None:
        logger.error("Failed to create element %s", element_name)
        exit(-1)
    return element


def get_v4l2_caps(device: str = "/dev/video0"):
    output = subprocess.check_output(["v4l2-ctl", "-d", device, "--list-formats-ext"])
    return output.decode().strip()


class CameraCapture:
    def __init__(self):
        self.pipeline = Gst.Pipeline.new("video-pipeline")
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::eos", self.on_eos)
        self.start = False

        self.idx = 0
        self.last_update = time.time()
        self.last_frame = None
        self.frame_availbable = threading.Event()

    def add_elements(self, elements: list[Gst.Element]):
        for element in elements:
            self.pipeline.add(element)

    def link_elements(self, elements: list[Gst.Element]):
        for i in range(len(elements) - 1):
            if not elements[i].link(elements[i + 1]):
                logger.error("Failed to link %s to %s", elements[i], elements[i + 1])
                exit(-1)
            else:
                logger.info("Linked %s to %s", elements[i], elements[i + 1])

    def on_eos(self, bus, msg):
        logger.warning("End-Of-Stream reached")
        self.pipeline.set_state(Gst.State.NULL)

    def on_new_sample(self, sink, data):
        sample = sink.emit("pull-sample")
        if sample is None:
            return Gst.FlowReturn.EOS

        buf = sample.get_buffer()
        caps = sample.get_caps()

        width = caps.get_structure(0).get_value("width")
        height = caps.get_structure(0).get_value("height")

        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR

        frame = np.ndarray((height, width, 3), buffer=map_info.data, dtype=np.uint8)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self.last_frame = frame
        self.frame_availbable.set()

        now = time.time()
        fps_monitor.tick()
        if now - self.last_update > 1:
            self.last_update = now
            print(f"FPS: {fps_monitor.fps:.1f}")

        self.idx += 1
        buf.unmap(map_info)
        return Gst.FlowReturn.OK

    def create(self):
        source = make_element("v4l2src")
        decoder = make_element("jpegdec")
        converter = make_element("videoconvert")
        capsfilter = make_element("capsfilter")
        sink = make_element("appsink")
        source.set_property("device", "/dev/video0")
        caps = Gst.Caps.from_string("video/x-raw,format=RGB,width=1920,height=1080,framerate=10/1")
        capsfilter.set_property("caps", caps)
        sink.set_property("emit-signals", True)
        sink.set_property("sync", False)
        sink.connect("new-sample", self.on_new_sample, None)

        self.add_elements([source, decoder, converter, capsfilter, sink])
        self.link_elements([source, decoder, converter, capsfilter, sink])

    def capture(self, timeout: float = 100) -> Optional[np.ndarray]:
        if not self.start:
            logger.info("Creating pipeline")
            self.create()
            logger.info("Setting pipeline to PLAY")
            self.pipeline.set_state(Gst.State.PLAYING)
            self.start = True

        timeout_s = timeout / 1000
        if self.frame_availbable.wait(timeout_s):
            frame = self.last_frame
            self.frame_availbable.clear()
            return frame
        logger.warning("Capture timeout (%s ms)", timeout)
        return None


if __name__ == "__main__":
    c = CameraCapture()
    caps = get_v4l2_caps()
    logger.info("Video Caps: %s", caps)
    while True:
        frame = c.capture(timeout=200)
        if frame is not None:
            print(frame.shape)
        else:
            logger.warning("Frame not ready...")
