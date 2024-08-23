import logging

from .. import functions
from .pipeline import AppSinkPipeline, UriSrcPipeline, V4l2Pipeline

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PipelineFactory:
    @classmethod
    def make(cls, input: str, options: dict) -> AppSinkPipeline:
        pipeline_classes = {
            "v4l2": V4l2Pipeline,
            "uri": UriSrcPipeline,
        }

        if functions.is_v4l2(input):
            return cls._create_pipeline(pipeline_classes["v4l2"], input, options)

        if input.startswith(("rtsp://", "file://")):
            return cls._create_pipeline(pipeline_classes["uri"], input, options)

        raise NotImplementedError(f"Input {input} not supported")

    @classmethod
    def _create_pipeline(cls, pipeline_class, input: str, options: dict) -> AppSinkPipeline:
        logger.info("Making %s pipeline", pipeline_class.__name__)
        pipeline = pipeline_class()
        pipeline.create(input, options)
        logger.info("Making %s pipeline DONE", pipeline_class.__name__)
        return pipeline
