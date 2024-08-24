import logging
from typing import Dict, Type

from .pipeline import (
    AppSrcPipeline,
    DisplaySinkPipeline,
    FileSinkPipeline,
    RtspSinkPipeline,
    TcpServerSinkPipeline,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PipelineFactory:
    @classmethod
    def make(cls, output: str, options) -> AppSrcPipeline:
        pipeline_classes: Dict[str, Type[AppSrcPipeline]] = {
            "rtsp://": RtspSinkPipeline,
            "tcp://": TcpServerSinkPipeline,
            "file://": FileSinkPipeline,
            "display://": DisplaySinkPipeline,
        }

        for prefix, pipeline_class in pipeline_classes.items():
            if output.startswith(prefix):
                logger.info("Creating %s", pipeline_class.__name__)
                pipeline = pipeline_class()
                pipeline.create(output, options)
                logger.info("Creating %s [DONE]", pipeline_class.__name__)
                return pipeline

        raise NotImplementedError(f"Output {output} not supported")
