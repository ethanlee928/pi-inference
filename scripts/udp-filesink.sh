#!/bin/bash

gst-launch-1.0 udpsrc port=5000 caps="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264,payload=(int)96" \
    ! rtph264depay ! h264parse ! matroskamux ! filesink location=output.mp4
