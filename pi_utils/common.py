import logging
from abc import abstractmethod

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
Gst.init(None)


class Pipeline:

    def __init__(self, pipeline_name: str):
        logger.info("Creating Gst Pipeline %s", pipeline_name)
        self.pipeline = Gst.Pipeline.new(pipeline_name)
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::eos", self.on_eos)

    @abstractmethod
    def create(self, *args, **kwargs):
        pass

    def on_eos(self, bus, msg):
        logger.warning("End-Of-Stream reached")
        self.set_null()

    def set_null(self):
        logger.warning("Set pipeline NULL")
        self.pipeline.set_state(Gst.State.NULL)

    def start(self):
        logger.info("Setting pipeline to PLAYING")
        self.pipeline.set_state(Gst.State.PLAYING)
