from pi_utils.hello import hello


def test_hello():
    res = hello()
    assert res == "World"
