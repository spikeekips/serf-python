import serf
import pytest


## requests

def test_request_must_be_checked_before_dumped () :
    _request = serf.request.BaseRequest()
    _request.command = 'anonymous_command'

    assert not _request.is_checked

    with pytest.raises(serf.UncheckedRequest, ) :
        str(_request, )

    _request.check(None, )
    str(_request, ) # nothing happened

    assert _request.is_checked


def test_request_stream_command () :
    _request = serf.request.BaseRequest()
    _request.command = 'anonymous_command'

    assert not _request.need_watching

    _request = serf.get_request_class('stream')(Type='*', )

    assert _request.need_watching


def test_request_add_callback_by_state_order () :
    _request = serf.request.BaseRequest()

    assert len(_request.callbacks) == 0

    _callbacks = list()
    for i in range(5, ) :
        _c = lambda x : None
        _c.func_name = 'callback_%d' % i

        _callbacks.append(_c, )
        _request.add_callback(_c, )

    assert _request.callbacks == _callbacks


class FakeRequest (serf.request.BaseRequest, ) :
    must_be_argument = ('a', 'a0', )


class FakeRequestWithOptional (serf.request.BaseRequest, ) :
    must_be_argument = ('a', 'a0', )
    optional_argument = ('b', 'b0', 'b1', )


def test_argument_check () :
    _request = FakeRequest()
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked

    _request = FakeRequest(a=0, )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked

    _request = FakeRequest(a=0, a0=1, )
    _request.check(None, )

    assert _request.is_checked


def test_argument_check_optional () :
    _request = FakeRequestWithOptional(a=0, a0=1, )
    _request.check(None, )

    assert _request.is_checked

    _request = FakeRequestWithOptional(a=0, a0=1, b=2, )
    _request.check(None, )

    assert _request.is_checked


def test_argument_check_unknown_key () :
    _request = FakeRequest(a=0, a0=1, c=9, )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked

    _request = FakeRequestWithOptional(a=0, a0=1, c=9, )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked


