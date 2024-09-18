<img src="https://github.com/ethanlee928/pi-inference/raw/main/images/raspberries-inference.jpg" width="75%" alt="raspberries-inference">

# pi-inference

Computer Vision Inference Pipeline for Raspberry Pi

## Dependencies

The pipeline is based on Gstreamer.

### Apt Packages

```bash
sudo scripts/install-packages.sh
```

## Development

Install the package using pip

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -e ".[dev]"
```
