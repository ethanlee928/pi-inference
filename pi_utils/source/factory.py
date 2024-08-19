import logging

from .. import functions
from .pipeline import AppSinkPipeline, UriSrcPipeline, V4l2Pipeline

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PipelineFactory:
    @classmethod
    def make(cls, input: str, **kwargs) -> AppSinkPipeline:
        if functions.is_v4l2(input):
            logger.info("Making V4L2 pipeline")
            pipeline = V4l2Pipeline()
            pipeline.create(input, **kwargs)
            logger.info("Making V4L2 pipeline DONE")
            return pipeline
        if input.startswith("rtsp://") or input.startswith("file://"):
            logger.info("Making URI pipeline")
            pipeline = UriSrcPipeline()
            pipeline.create(input, **kwargs)
            logger.info("Making URI pipeline DONE")
            return pipeline
        raise NotImplementedError("Input %s not supported", input)
