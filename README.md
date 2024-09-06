# pi-utils

Multimedia utilities for Raspberry Pi

## Dependencies

The pipeline is based on Gstreamer.

### Apt Packages

```bash
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
```

### Python Packages

```bash
pip3 install -r requirements.txt
```

## Development

Install the package using pip

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -e ".[dev]"
```
