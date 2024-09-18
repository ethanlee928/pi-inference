import logging

from .pipeline import (
    AppSinkPipeline,
    LibcameraPipeline,
    PiCameraPipeline,
    UriSrcPipeline,
    V4l2Pipeline,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PipelineFactory:
    @classmethod
    def make(cls, input: str, options: dict) -> AppSinkPipeline:
        pipeline_classes = {
            "v4l2://": V4l2Pipeline,
            "rtsp://": UriSrcPipeline,
            "file://": UriSrcPipeline,
            "csi://": LibcameraPipeline,
            "picam://": PiCameraPipeline,
        }

        for prefix, pipeline_class in pipeline_classes.items():
            if input.startswith(prefix):
                logger.info("Creating %s", pipeline_class.__name__)
                pipeline = pipeline_class()
                pipeline.create(input, options)
                logger.info("Creating %s [DONE]", pipeline_class.__name__)
                return pipeline

        raise NotImplementedError(f"Input {input} not supported")
