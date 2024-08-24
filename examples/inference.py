import argparse
import logging
import sys
import time

import gi
import numpy as np
import supervision as sv
from ncnn.model_zoo import get_model

from pi_utils import VideoOutput, VideoSource
from pi_utils import functions as f

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_optional_args(args: list):
    return {arg.lstrip("-"): value for arg, value in zip(args[::2], args[1::2])}


def main(args, options):
    last_update = time.time()
    fps_monitor = sv.FPSMonitor()

    video_source = VideoSource(args.input, options=options)
    video_output = VideoOutput(args.output, options=options)

    net = get_model(
        "yolov8s",
        target_size=640,
        prob_threshold=0.25,
        nms_threshold=0.45,
        num_threads=4,
        use_gpu=False,
    )
    box_annotator = sv.BoxAnnotator()
    labels_annotator = sv.LabelAnnotator()

    while True:
        try:
            frame = video_source.capture(timeout=300)
            now = time.time()
            if frame is not None:
                fps_monitor.tick()
                objects = net(frame)
                xyxy = []
                confidence = []
                class_id = []
                for obj in objects:
                    x, y, w, h = obj.rect.x, obj.rect.y, obj.rect.w, obj.rect.h
                    xyxy.append([x, y, x + w, y + h])
                    confidence.append(obj.prob)
                    class_id.append(int(obj.label))
                detections = (
                    sv.Detections(xyxy=np.array(xyxy), confidence=np.array(confidence), class_id=np.array(class_id))
                    if len(objects) > 0
                    else sv.Detections.empty()
                )
                detections.data["class_name"] = [net.class_names[_id] for _id in class_id]
                labels = [
                    f"{class_name} {confidence:.2f}"
                    for class_name, confidence in zip(detections["class_name"], detections.confidence)
                ]

                frame = box_annotator.annotate(scene=frame, detections=detections)
                frame = labels_annotator.annotate(scene=frame, detections=detections, labels=labels)
                frame = f.draw_clock(frame)
                video_output.render(frame)
                if now - last_update > 1:
                    last_update = now
                    logger.info("FPS: %.1f, frame shape: %s", fps_monitor.fps, frame.shape)
        except KeyboardInterrupt:
            break

    video_source.on_terminate()
    video_output.on_terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Streaming Application")
    parser.add_argument("input", type=str, help="Input URI for the video source")
    parser.add_argument("output", type=str, help="Output URI for the video stream")
    opts, extra_opts = parser.parse_known_args()
    sys.exit(main(opts, extract_optional_args(extra_opts)))
