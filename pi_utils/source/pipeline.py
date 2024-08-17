import logging
import threading
from abc import ABC, abstractmethod

import cv2
import gi
import numpy as np
from gi.repository import Gst
from typing_extensions import override

from ..functions import add_elements, link_elements, make_element

gi.require_version("Gst", "1.0")
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Pipeline(ABC):
    Gst.init(None)

    def __init__(self) -> None:
        self.pipeline = Gst.Pipeline.new("video-pipeline")
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::eos", self.on_eos)

        self.last_frame = None
        self.frame_available = threading.Event()

    @abstractmethod
    def create(self, **kwargs):
        pass

    def on_eos(self, bus, msg):
        logger.warning("End-Of-Stream reached")
        self.set_null()

    def set_null(self):
        logger.warning("Set pipeline NULL")
        self.pipeline.set_state(Gst.State.NULL)

    def on_rgb_sample(self, sink, data):
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
        self.frame_available.set()

        buf.unmap(map_info)
        return Gst.FlowReturn.OK

    def start(self):
        logger.info("Setting pipeline to PLAYING")
        self.pipeline.set_state(Gst.State.PLAYING)


class V4l2Pipeline(Pipeline):
    @override
    def create(self, input, **kwargs):
        elements = []
        source = make_element("v4l2src")
        elements.append(source)
        if kwargs.get("codec") is not None:
            logger.info("Using MJPG")
            decoder = make_element("jpegdec")
            elements.append(decoder)
        else:
            logger.info("Using YUYV")
        converter = make_element("videoconvert")
        capsfilter = make_element("capsfilter")
        sink = make_element("appsink")
        source.set_property("device", input)
        caps = Gst.Caps.from_string(
            "video/x-raw,format=RGB,width={},height={},framerate={}/1".format(
                kwargs["width"], kwargs["height"], kwargs["framerate"]
            )
        )
        capsfilter.set_property("caps", caps)
        sink.set_property("emit-signals", True)
        sink.set_property("sync", False)
        sink.connect("new-sample", self.on_rgb_sample, None)
        elements += [converter, capsfilter, sink]

        add_elements(self.pipeline, elements)
        link_elements(elements)
