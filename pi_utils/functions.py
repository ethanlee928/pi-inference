import logging
import re

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


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
