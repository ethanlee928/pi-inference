import logging
import re
import threading
from abc import ABC, abstractmethod
from typing import Optional

import cv2
import gi
import numpy as np
from gi.repository import Gst

gi.require_version("Gst", "1.0")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def is_v4l2(input: str):
    v4l2_pattern = r"^(/dev/video\d+|\d+)$"
    return re.match(v4l2_pattern, input) is not None


def add_elements(pipeline: Gst.Pipeline, elements: list[Gst.Element]):
    for element in elements:
        pipeline.add(element)


def link_elements(elements: list[Gst.Element]):
    for i in range(len(elements) - 1):
        if not elements[i].link(elements[i + 1]):
            logger.error("Failed to link %s to %s", elements[i], elements[i + 1])
            exit(-1)
        else:
            logger.info("Linked %s to %s", elements[i], elements[i + 1])


def make_element(element_name, name=None):
    _name = element_name if name is None else name
    element = Gst.ElementFactory.make(element_name, _name)
    if element is None:
        logger.error("Failed to create element %s", element_name)
        exit(-1)
    logger.info("Created %s", element)
    return element


# class PipelineFactory:
#     _pipeline: Gst.Pipeline = Gst.Pipeline.new("pipeline")

#     @classmethod
#     def _v4l2src(
#         cls,
#         input: str,
#         width: int,
#         height: int,
#         framerate: int,
#         codec: Optional[str] = "mjpeg",
#     ):
#         source = make_element("v4l2src")
#         converter = make_element("videoconvert")
#         capsfilter = make_element("capsfilter")
#         sink = make_element("appsink")
#         source.set_property("device", input)
#         caps = Gst.Caps.from_string(
#             "video/x-raw,format=RGB,width={},height={},framerate={}/1".format(
#                 width, height, framerate
#             )
#         )
#         capsfilter.set_property("caps", caps)
#         sink.set_property("emit-signals", True)
#         sink.set_property("sync", False)
#         sink.connect("new-sample", self.on_new_sample, None)

#         if codec is None:
#             logger.info("No codec specify, will use YUYV")

#         return cls._pipeline

#     @classmethod
#     def make(cls, input: str, **kwargs):
#         if is_v4l2(input):
#             return cls._v4l2src(input, kwargs["width"], kwargs["height"])
#         else:
#             raise NotImplementedError("Input %s not supported", input)


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


class VideoSource:
    # NOTE: This act as high level factory
    def __init__(self, input: str, **kwargs) -> None:
        self.input = input
        self.initialized = False
        self.pipeline = V4l2Pipeline()
        self.pipeline.create(input, **kwargs)

    def on_terminate(self):
        self.pipeline.set_null()

    def capture(self, timeout: float = 100) -> Optional[np.ndarray]:
        if not self.initialized:
            self.initialized = True
            self.pipeline.start()

        timeout_s = timeout / 1000
        if self.pipeline.frame_available.wait(timeout_s):
            frame = self.pipeline.last_frame
            self.pipeline.frame_available.clear()
            return frame
        logger.warning("Capture timeout (%s ms)", timeout)
        return None
