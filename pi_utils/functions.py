import logging
import re
from datetime import datetime
from typing import Optional

import gi
import numpy as np
import supervision as sv

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst, GstRtspServer

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


def is_v4l2(input: str):
    """
    Checks if the given input is a valid V4L2 device.

    Args:
        input (str): The input string to be checked.

    Returns:
        bool: True if the input is a valid V4L2 device, False otherwise.
    """
    v4l2_pattern = r"^(/dev/video\d+|\d+)$"
    return re.match(v4l2_pattern, input) is not None


def extract_rtsp(input: str) -> tuple[str, str, str]:
    """
    Extracts the IP address, port, and base from an RTSP URL.

    Args:
        input (str): The RTSP URL string.

    Returns:
        tuple[str, str, str]: A tuple containing the extracted IP address, port, and base.
    """
    if not input.startswith("rtsp://"):
        raise ValueError("Input string is not an RTSP URL.")

    ip = re.search(r"//([^:]+)", input).group(1)
    port = re.search(r":(\d+)", input).group(1)
    base = re.search(r"/([^/?]+)$", input).group(1)
    return ip, port, base


def add_elements(pipeline: Gst.Pipeline, elements: list[Gst.Element]):
    """
    Adds the given elements to the pipeline.

    Args:
        pipeline (Gst.Pipeline): The pipeline to add the elements to.
        elements (list[Gst.Element]): The list of elements to add to the pipeline.
    """
    for element in elements:
        pipeline.add(element)


def link_elements(elements: list[Gst.Element]):
    """
    Links a list of GStreamer elements together.

    Args:
        elements (list[Gst.Element]): A list of GStreamer elements.

    Returns:
        None

    Raises:
        SystemExit: If linking fails.

    """
    for i in range(len(elements) - 1):
        if not elements[i].link(elements[i + 1]):
            logger.error("Failed to link %s to %s", elements[i], elements[i + 1])
            exit(-1)
        else:
            logger.debug("Linked %s to %s", elements[i], elements[i + 1])


def make_element(element_name: str, name=None):
    """
    Create a GStreamer element with the given element_name and optional name.

    Args:
        element_name (str): The name of the GStreamer element to create.
        name (str, optional): The name to assign to the created element. If not provided, the element_name will be used.

    Returns:
        Gst.Element: The created GStreamer element.

    Raises:
        SystemExit: If the element creation fails.

    """
    _name = element_name if name is None else name
    element = Gst.ElementFactory.make(element_name, _name)
    if element is None:
        logger.error("Failed to create element %s", element_name)
        exit(-1)
    logger.debug("Created %s", element)
    return element


def launch_rtsp_server(
    rtsp_port=8554,
    udp_port=5000,
    codec="H264",
    clock_rate=90000,
    payload=96,
    endpoint="base",
):
    """Set up and run an RTSP server with configurable parameters.

    Args:
        rtsp_port (int): Port for the RTSP server.
        udp_port (int): Port for the UDP source.
        codec (str): Video codec to be used.
        clock_rate (int): Clock rate for the stream.
        payload (int): Payload type for the stream.
        endpoint (str): Endpoint for the stream. e.g., rtsp://@:8554/base
    """
    server = GstRtspServer.RTSPServer()
    server.set_property("service", str(rtsp_port))

    factory = GstRtspServer.RTSPMediaFactory()
    factory.set_shared(True)

    pipeline = (
        "( udpsrc port={udp_port} name=pay0 "
        "caps=application/x-rtp,media=video,clock-rate={clock_rate},"
        "encoding-name=(string){codec},payload={payload} )"
    ).format(udp_port=udp_port, codec=codec, clock_rate=clock_rate, payload=payload)

    factory.set_launch(pipeline)
    mount_points = server.get_mount_points()
    mount_points.add_factory(f"/{endpoint}", factory)
    server.attach(None)

    loop = GLib.MainLoop()
    loop.run()
    logger.warning("Exit RTSP Server MainLoop ...")


def draw_clock(frame: np.ndarray, anchor_x: Optional[int] = None, anchor_y: Optional[int] = None):
    anchor_x = anchor_x or 100
    anchor_y = anchor_y or 20

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_anchor = sv.Point(anchor_x, anchor_y)
    frame = sv.draw_text(
        scene=frame,
        text=current_time,
        text_anchor=text_anchor,
        text_color=sv.Color.WHITE,
        background_color=sv.Color.BLACK,
    )
    return frame
