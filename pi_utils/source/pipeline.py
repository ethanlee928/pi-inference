import logging
import threading

import cv2
import gi
import numpy as np
from typing_extensions import override

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from ..common import Pipeline
from ..functions import add_elements, link_elements, make_element

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


class AppSinkPipeline(Pipeline):

    def __init__(self):
        super().__init__(pipeline_name=AppSinkPipeline.__name__)
        self.last_frame = None
        self.frame_available = threading.Event()

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


class V4l2Pipeline(AppSinkPipeline):
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
