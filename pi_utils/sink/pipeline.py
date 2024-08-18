import logging
import threading

import gi
import numpy as np
from typing_extensions import override

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from .. import functions as f
from ..common import Pipeline

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


class AppSrcPipeline(Pipeline):
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


class RtspSinkPipeline(AppSrcPipeline):
    UDP_HOST = "0.0.0.0"
    UDP_PORT = 5000
    UDP_PAYLOAD = 96

    @override
    def create(self, output: str, **kwargs):
        _, port, base = f.extract_rtsp(output)
        width, height, framerate = kwargs["width"], kwargs["height"], kwargs["framerate"]
        self.appsrc.set_property(
            "caps",
            Gst.Caps.from_string(f"video/x-raw,format=BGR,width={width},height={height},framerate={framerate}/1"),
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
