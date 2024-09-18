import logging
import re
import time
from collections import deque
from datetime import datetime
from typing import Optional

import cv2
import gi
import numpy as np

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
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


def extract_tcp(input: str):
    """
    Extracts the IP address and port from a TCP URL.

    Args:
        input (str): The TCP URL string.

    Returns:
        tuple[str, str]: A tuple containing the extracted IP address and port.
    """
    if not input.startswith("tcp://"):
        raise ValueError("Input string is not a TCP URL.")

    ip = re.search(r"//([^:]+)", input).group(1)
    port = re.search(r":(\d+)", input).group(1)
    return ip, port


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
    width, height = frame.shape[1], frame.shape[0]
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    font_scale = 0.5
    font_thickness = 1
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(current_time, font, font_scale, font_thickness)[0]
    padding = 5

    anchor_x = anchor_x or 50 + padding
    anchor_y = anchor_y or 50 + padding

    top = max(0, anchor_y - text_size[1] - padding)
    bottom = min(height, anchor_y + padding)
    left = max(0, anchor_x - padding)
    right = min(width, anchor_x + text_size[0] + padding)

    sub_frame = frame[top:bottom, left:right]
    black_rect = np.ones(sub_frame.shape, dtype=np.uint8) * 10

    res = cv2.addWeighted(sub_frame, 0.5, black_rect, 0.5, 1.0)
    frame[top:bottom, left:right] = res

    cv2.putText(frame, current_time, (anchor_x, anchor_y), font, font_scale, (255, 255, 255), font_thickness)
    return frame


class FPSMonitor:
    """
    A class for monitoring frames per second (FPS) to benchmark latency.
    """

    def __init__(self, sample_size: int = 30):
        """
        Args:
            sample_size (int): The maximum number of observations for latency
                benchmarking.
        """
        self.all_timestamps = deque(maxlen=sample_size)

    @property
    def fps(self) -> float:
        """
        Computes and returns the average FPS based on the stored time stamps.

        Returns:
            float: The average FPS. Returns 0.0 if no time stamps are stored.
        """
        if not self.all_timestamps:
            return 0.0
        taken_time = self.all_timestamps[-1] - self.all_timestamps[0]
        return (len(self.all_timestamps)) / taken_time if taken_time != 0 else 0.0

    def tick(self) -> None:
        """
        Adds a new time stamp to the deque for FPS calculation.
        """
        self.all_timestamps.append(time.monotonic())

    def reset(self) -> None:
        """
        Clears all the time stamps from the deque.
        """
        self.all_timestamps.clear()