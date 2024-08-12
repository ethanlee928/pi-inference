#!/bin/bash

gst-launch-1.0 v4l2src device=/dev/video0 \
    ! jpegdec ! videoconvert \
    ! x264enc ! h264parse ! rtph264pay pt=96 ! queue \
    ! udpsink host=0.0.0.0 port=5000 async=false
