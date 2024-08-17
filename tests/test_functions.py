import pytest

import pi_utils.functions as functions


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
