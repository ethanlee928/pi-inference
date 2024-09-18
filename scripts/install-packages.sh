#!/bin/bash

sudo apt-get update
sudo apt-get install gstreamer1.0

# For Debug Graph
sudo apt-get install graphviz

# PyGObject
sudo apt install libcairo2-dev libxt-dev libgirepository1.0-dev

# For RTSP Server
sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstrtspserver-1.0-dev gstreamer1.0-rtsp

# v4l2-ctl
sudo apt-get install v4l-utils
