import importlib
import logging
import threading

import gi
import numpy as np

if not importlib.util.find_spec("libcamera") or not importlib.util.find_spec("picamera2"):
    from unittest.mock import Mock

    libcamera = Mock()
    picamera2 = Mock()
else:
    import libcamera
    import picamera2

from typing_extensions import override

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from ..common import GstPipeline, Pipeline
from ..functions import add_elements, link_elements, make_element

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


class AppSinkPipeline(GstPipeline):

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

        frame = np.ndarray((height, width, 3), buffer=map_info.data, dtype=np.uint8).copy()
        self.last_frame = frame
        self.frame_available.set()

        buf.unmap(map_info)
        return Gst.FlowReturn.OK


class UriSrcPipeline(AppSinkPipeline):
    @staticmethod
    def pad_added_handler(decodebin, pad, converter):
        converter_static_sink_pad = converter.get_static_pad("sink")
        if converter_static_sink_pad.is_linked():
            logger.info("Sink pad is already linked")
            return
        if pad.link(converter_static_sink_pad) != Gst.PadLinkReturn.OK:
            logger.error("Failed to link decodebin to converter")
            return Gst.FlowReturn.ERROR

    @override
    def create(self, resource_uri: str, options: dict):
        width = options.get("input-width") or options.get("width") or 1280
        height = options.get("input-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        uridecodebin = make_element("uridecodebin")
        converter = make_element("videoconvert")
        capsfilter = make_element("capsfilter")
        sink = make_element("appsink")
        sink.set_property("emit-signals", True)
        sink.set_property("sync", options.get("sync", True))
        sink.connect("new-sample", self.on_rgb_sample, None)

        uridecodebin.set_property("uri", resource_uri)
        uridecodebin.connect("pad-added", self.pad_added_handler, converter)
        caps = Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1")
        capsfilter.set_property("caps", caps)
        add_elements(self.pipeline, [uridecodebin, converter, capsfilter, sink])
        link_elements([converter, capsfilter, sink])


class V4l2Pipeline(AppSinkPipeline):
    @override
    def create(self, resource_uri: str, options: dict):
        device = resource_uri.replace("v4l2://", "")
        elements = []
        width = options.get("input-width") or options.get("width") or 1280
        height = options.get("input-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        source = make_element("v4l2src")
        elements.append(source)
        codec = options.get("codec")
        if codec is None:
            logger.info("Using YUYV")
        elif str(codec).lower() == "mjpg":
            logger.info("Using MJPG")
            decoder = make_element("jpegdec")
            elements.append(decoder)
        else:
            raise NotImplementedError("v4l2 pipeline currently supports MJPG and YUYV only")
        converter = make_element("videoconvert")
        capsfilter = make_element("capsfilter")
        sink = make_element("appsink")
        source.set_property("device", device)
        caps = Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1")
        capsfilter.set_property("caps", caps)
        sink.set_property("emit-signals", True)
        sink.set_property("sync", False)
        sink.connect("new-sample", self.on_rgb_sample, None)
        elements += [converter, capsfilter, sink]

        add_elements(self.pipeline, elements)
        link_elements(elements)


class LibcameraPipeline(AppSinkPipeline):
    @override
    def create(self, resource_uri: str, options: dict):
        device = resource_uri.replace("csi://", "")
        width = options.get("input-width") or options.get("width") or 1280
        height = options.get("input-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        source = make_element("libcamerasrc")
        if device:
            source.set_property("camera-name", device)

        capsfilter_1 = make_element("capsfilter", name="capsfilter_1")
        caps_1 = Gst.Caps.from_string(
            f"video/x-raw,colorimetry=bt709,format=NV12,width={width},height={height},framerate={framerate}/1"
        )
        capsfilter_1.set_property("caps", caps_1)

        videoconvert = make_element("videoconvert")

        capsfilter_2 = make_element("capsfilter", name="capsfilter_2")
        caps_2 = Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1")
        capsfilter_2.set_property("caps", caps_2)

        sink = make_element("appsink")
        sink.set_property("emit-signals", True)
        sink.set_property("sync", False)
        sink.connect("new-sample", self.on_rgb_sample, None)

        elements = [source, capsfilter_1, videoconvert, capsfilter_2, sink]
        add_elements(self.pipeline, elements)
        link_elements(elements)


class PiCameraPipeline(Pipeline):
    def __init__(self):
        self.last_frame = None
        self.frame_available = threading.Event()
        self.picam = None

    def on_request(self, request):
        with picamera2.MappedArray(request, "main") as m:
            self.last_frame = m.array.copy()
            self.frame_available.set()

    @override
    def create(self, resource_uri: str, options: dict):
        camera_number = resource_uri.replace("picam://", "")
        format = "BGR888"  # Hardcoded for RGB array
        width = options.get("input-width") or options.get("width") or 1280
        height = options.get("input-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        hflip, vflip = options.get("hflip", 0), options.get("vflip", 0)
        auto_focus = options.get("auto-focus", 0)
        self.picam = picamera2.Picamera2(0 if camera_number == "" else int(camera_number))
        transforma = libcamera.Transform(vflip=vflip, hflip=hflip)
        config = self.picam.create_video_configuration(
            main={"size": (int(width), int(height)), "format": format},
            transform=transforma,
        )
        self.picam.configure(config)
        if auto_focus:
            self.picam.set_controls({"AfMode": libcamera.controls.AfModeEnum.Continuous, "FrameRate": int(framerate)})

        self.picam.post_callback = self.on_request

    @override
    def start(self):
        logger.info("Starting %s", PiCameraPipeline.__name__)
        self.picam.start()

    @override
    def terminate(self):
        logger.info("Stopping %s", PiCameraPipeline.__name__)
        self.picam.stop()
