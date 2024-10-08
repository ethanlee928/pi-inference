import re

import setuptools
from setuptools import find_packages

with open("./pi_inference/__init__.py", "r") as f:
    content = f.read()
    # from https://www.py4u.net/discuss/139845
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content).group(1)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pi_inference",
    version=version,
    author="ethanlee",
    author_email="ethan2000.el@gmail.com",
    description="pi-inference",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethanlee928/pi-inference",
    install_requires=[
        "pycairo",
        "PyGObject",
        "numpy",
        "opencv-python",
        "typing-extensions",
        "ncnn",
        "supervision",
    ],
    packages=find_packages(exclude=("tests",)),
    package_dir={"": "."},
    extras_require={
        "dev": ["flake8", "black==24.8.0", "isort", "twine", "pytest", "wheel"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
