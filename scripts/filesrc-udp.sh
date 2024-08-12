#!/bin/bash

file=${1}

gst-launch-1.0 filesrc location=${file} \
    ! qtdemux ! h265parse ! avdec_h265 ! videoconvert \
    ! x264enc ! h264parse ! rtph264pay pt=96 ! queue \
    ! udpsink host=0.0.0.0 port=5000 async=false
