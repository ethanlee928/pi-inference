import logging

from .pipeline import AppSrcPipeline, RtspSinkPipeline

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PipelineFactory:
    @classmethod
    def make(cls, output: str, **kwargs) -> AppSrcPipeline:
        if output.startswith("rtsp://"):
            logger.info("Creating RTSP Sink Pipeline")
            pipeline = RtspSinkPipeline()
            pipeline.create(output, **kwargs)
            return pipeline
        raise NotImplementedError("Output %s not supported", output)
