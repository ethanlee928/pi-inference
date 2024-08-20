import logging

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
    def make(cls, output: str, **kwargs) -> AppSrcPipeline:
        if output.startswith("rtsp://"):
            logger.info("Creating RTSP Sink Pipeline")
            pipeline = RtspSinkPipeline()
            pipeline.create(output, **kwargs)
            return pipeline
        if output.startswith("tcp://"):
            logger.info("Creating TCP Server Sink Pipeline")
            pipeline = TcpServerSinkPipeline()
            pipeline.create(output, **kwargs)
            return pipeline
        if output.startswith("file://"):
            logger.info("Creating File Sink Pipeline")
            pipeline = FileSinkPipeline()
            pipeline.create(output, **kwargs)
            return pipeline
        if output.startswith("display://"):
            logger.info("Creating Display Sink Pipeline")
            pipeline = DisplaySinkPipeline()
            pipeline.create(output, **kwargs)
            return pipeline
        raise NotImplementedError("Output %s not supported" % output)
