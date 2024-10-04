<img src="https://github.com/ethanlee928/pi-inference/raw/main/images/raspberries-inference.jpg" width="75%" alt="raspberries-inference">

# pi-inference

A Computer Vision Inference Pipeline for Raspberry Pi inspired by [Jetson Inference](https://github.com/dusty-nv/jetson-inference).

The pipeline utilized `Gstreamer` and [`picamera2`](https://github.com/raspberrypi/picamera2) for video pipeline, and [`ncnn`](https://github.com/Tencent/ncnn) for optimized inference.

## 🖥️ Install

The pipeline is based on Gstreamer v1.22.0.

```bash
sudo scripts/install-packages.sh
```

Install the `pi-inference` package in a `Python>=3.8` environment.

```bash
pip install pi-inference
```

## 🚀 Quick Start

Inference using USB camera with pretrained `YOLOv8s` model, and display on GUI window.

```python
import logging

import supervision as sv
from ncnn.model_zoo import get_model

from pi_inference import VideoOutput, VideoSource
from pi_inference import functions as f

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

video_source = VideoSource("v4l2:///dev/video0", {"codec": "mjpg"})
video_output = VideoOutput("display://0", {})

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
fps_monitor = sv.FPSMonitor()

while True:
    try:
        frame = video_source.capture(timeout=300)
        if frame is not None:
            fps_monitor.tick()
            detections = f.from_ncnn(frame, net)
            labels = [
                f"{class_name} {confidence:.2f}"
                for class_name, confidence in zip(detections["class_name"], detections.confidence)
            ]
            frame = box_annotator.annotate(scene=frame, detections=detections)
            frame = labels_annotator.annotate(scene=frame, detections=detections, labels=labels)
            frame = f.draw_clock(frame)
            frame = f.draw_text(frame, f"FPS: {fps_monitor.fps:.1f}", anchor_y=80)
            video_output.render(frame)

    except KeyboardInterrupt:
        break

video_source.on_terminate()
video_output.on_terminate()
```

Find out more in [`examples`](examples).

## ⛏️ Development

Install the package using pip

```bash
# For raspberrypi
python3 -m venv --system-site-packages .venv

# For others
python3 -m venv .venv

source .venv/bin/activate
pip3 install --upgrade pip
pip3 install -e ".[dev]"
```
