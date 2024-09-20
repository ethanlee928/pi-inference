import logging
import threading

import gi
import numpy as np
from typing_extensions import override

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from .. import functions as f
from ..common import GstPipeline

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


class AppSrcPipeline(GstPipeline):
    def __init__(self) -> None:
        super().__init__(pipeline_name=AppSrcPipeline.__name__)
        self.appsrc = f.make_element("appsrc")
        self.appsrc.set_property("is-live", True)
        self.appsrc.set_property("block", True)
        self.appsrc.set_property("format", Gst.Format.TIME)

    def on_frame(self, frame: np.ndarray):
        buffer = Gst.Buffer.new_wrapped(frame.tobytes())
        buffer.pts = self.appsrc.get_current_running_time()
        buffer.dts = Gst.CLOCK_TIME_NONE
        buffer.duration = Gst.CLOCK_TIME_NONE
        result = self.appsrc.emit("push-buffer", buffer)
        if result != Gst.FlowReturn.OK:
            logger.critical("Failed to push buffer: %s", result)


class FileSinkPipeline(AppSrcPipeline):
    @override
    def create(self, resource_uri: str, options: dict):
        filepath = resource_uri.replace("file://", "")
        width = options.get("output-width") or options.get("width") or 1280
        height = options.get("output-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        self.appsrc.set_property(
            "caps",
            Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1"),
        )
        videoconvert = f.make_element("videoconvert")
        encoder = f.make_element("x264enc")
        mux = f.make_element("matroskamux")
        filesink = f.make_element("filesink")
        filesink.set_property("location", filepath)
        f.add_elements(self.pipeline, [self.appsrc, videoconvert, encoder, mux, filesink])
        f.link_elements([self.appsrc, videoconvert, encoder, mux, filesink])
        logger.info("Saving video @ %s", filepath)


class TcpServerSinkPipeline(AppSrcPipeline):
    @override
    def create(self, resource_uri: str, options: dict):
        host, port = f.extract_tcp(resource_uri)
        width = options.get("output-width") or options.get("width") or 1280
        height = options.get("output-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        self.appsrc.set_property(
            "caps",
            Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1"),
        )
        encoder = f.make_element("jpegenc")
        multipartmux = f.make_element("multipartmux")
        tcpserversink = f.make_element("tcpserversink")
        tcpserversink.set_property("host", host)
        tcpserversink.set_property("port", int(port))
        f.add_elements(self.pipeline, [self.appsrc, encoder, multipartmux, tcpserversink])
        f.link_elements([self.appsrc, encoder, multipartmux, tcpserversink])
        logger.info("View TCP stream @ tcp://%s:%s", host, port)


class RtspSinkPipeline(AppSrcPipeline):
    UDP_HOST = "0.0.0.0"
    UDP_PORT = 5000
    UDP_PAYLOAD = 96

    @override
    def create(self, resource_uri: str, options: dict):
        _, port, base = f.extract_rtsp(resource_uri)
        width = options.get("output-width") or options.get("width") or 1280
        height = options.get("output-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        self.appsrc.set_property(
            "caps",
            Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1"),
        )
        videoconvert = f.make_element("videoconvert")
        encoder = f.make_element("x264enc")
        rtph264pay = f.make_element("rtph264pay")
        queue = f.make_element("queue")
        udpsink = f.make_element("udpsink")
        udpsink.set_property("host", RtspSinkPipeline.UDP_HOST)
        udpsink.set_property("port", RtspSinkPipeline.UDP_PORT)
        udpsink.set_property("async", False)
        rtph264pay.set_property("pt", RtspSinkPipeline.UDP_PAYLOAD)
        f.add_elements(self.pipeline, [self.appsrc, videoconvert, encoder, rtph264pay, queue, udpsink])
        f.link_elements([self.appsrc, videoconvert, encoder, rtph264pay, queue, udpsink])

        threading.Thread(
            target=f.launch_rtsp_server,
            kwargs={
                "rtsp_port": port,
                "udp_port": RtspSinkPipeline.UDP_PORT,
                "payload": RtspSinkPipeline.UDP_PAYLOAD,
                "endpoint": base,
            },
            daemon=True,
        ).start()
        logger.info("RTSP server started at rtsp://@:%s/%s", port, base)


class DisplaySinkPipeline(AppSrcPipeline):
    @override
    def create(self, resource_uri: str, options: dict):
        width = options.get("output-width") or options.get("width") or 1280
        height = options.get("output-height") or options.get("height") or 720
        framerate = options.get("framerate", 30)
        self.appsrc.set_property(
            "caps",
            Gst.Caps.from_string(f"video/x-raw,format=RGB,width={width},height={height},framerate={framerate}/1"),
        )
        videoconvert = f.make_element("videoconvert")
        autovideosink = f.make_element("autovideosink")
        f.add_elements(self.pipeline, [self.appsrc, videoconvert, autovideosink])
        f.link_elements([self.appsrc, videoconvert, autovideosink])
