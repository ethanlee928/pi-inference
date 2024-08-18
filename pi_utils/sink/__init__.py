import logging

import numpy as np

from .factory import PipelineFactory

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class VideoOutput:
    def __init__(self, output: str, **kwargs):
        self.output = output
        self.initialized = False
        self.pipeline = PipelineFactory.make(output, **kwargs)

    def on_terminate(self):
        self.pipeline.set_null()

    def render(self, frame: np.ndarray):
        if not self.initialized:
            self.initialized = True
            self.pipeline.start()
        self.pipeline.on_frame(frame)
