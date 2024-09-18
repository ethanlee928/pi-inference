import pytest

import pi_inference.functions as functions


def test_is_v4l2():
    assert functions.is_v4l2("/dev/video0")
    assert functions.is_v4l2("0")
    assert functions.is_v4l2("1")
    assert not functions.is_v4l2("video0")
    assert not functions.is_v4l2("video1")


def test_make_element():
    element = functions.make_element("fakesink")
    assert element.get_name() == "fakesink"
    with pytest.raises(SystemExit):
        functions.make_element("non_existent_element")


def test_extract_rtsp():
    ip, port, base = functions.extract_rtsp("rtsp://0.0.0.0:8554/base")
    assert ip == "0.0.0.0"
    assert port == "8554"
    assert base == "base"

    ip, port, base = functions.extract_rtsp("rtsp://@:8555/camera")
    assert ip == "@"
    assert port == "8555"
    assert base == "camera"

    with pytest.raises(ValueError):
        functions.extract_rtsp("http://@:8555/camera")
