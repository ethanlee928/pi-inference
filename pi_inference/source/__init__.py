import logging
from typing import Optional

import numpy as np

from .factory import PipelineFactory

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class VideoSource:
    def __init__(self, input: str, options: dict) -> None:
        self.input = input
        self.initialized = False
        self.pipeline = PipelineFactory.make(input, options)

    def on_terminate(self):
        self.pipeline.terminate()

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
