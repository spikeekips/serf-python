import serf
import pytest
import msgpack


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

    assert not _request.is_stream

    _request.command = serf.constant.STREAM_COMMANDS[0]

    assert _request.is_stream

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


class TestRequest (serf.request.BaseRequest, ) :
    must_be_argument = ('a', 'a0', )


class TestRequestWithOptional (serf.request.BaseRequest, ) :
    must_be_argument = ('a', 'a0', )
    optional_argument = ('b', 'b0', 'b1', )


def test_argument_check () :
    _request = TestRequest()
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked

    _request = TestRequest(a=0, )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked

    _request = TestRequest(a=0, a0=1, )
    _request.check(None, )

    assert _request.is_checked


def test_argument_check_optional () :
    _request = TestRequestWithOptional(a=0, a0=1, )
    _request.check(None, )

    assert _request.is_checked

    _request = TestRequestWithOptional(a=0, a0=1, b=2, )
    _request.check(None, )

    assert _request.is_checked


def test_argument_check_unknown_key () :
    _request = TestRequest(a=0, a0=1, c=9, )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked

    _request = TestRequestWithOptional(a=0, a0=1, c=9, )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked


## command request

class FakeClient :
    ipc_version = serf.constant.DEFAULT_IPC_VERSION


def test_request_handshake () :
    _request = serf.get_request_class('handshake')()
    _request.check(FakeClient, )

    assert _request.is_checked
    assert 'Version' in _request.body
    assert _request.body.get('Version') == FakeClient.ipc_version


def test_request_event () :
    _body = dict(
            Name='anonymous-event',
            Payload='payload',
        )

    _request = serf.get_request_class('event')(**_body)
    _request.check(None, )

    assert _request.is_checked

    # `Coalesce` is not bool type
    _body = dict(
            Name='anonymous-event',
            Payload='payload',
            Coalesce=1,
        )

    _request = serf.get_request_class('event')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked


def test_request_event_payload_size_limit () :
    _body_normal = dict(
            Name='anonymous-event',
            Payload='payload',
        )
    _request = serf.get_request_class('event')(**_body_normal)
    _request.check(None, )

    assert _request.is_checked

    _dumped = ''

    _n = 10
    _body_without_payload = dict(Name='anonymous-event', Payload='', )
    while len(_dumped) < serf.constant.PAYLOAD_SIZE_LIMIT :
        _body_without_payload['Payload'] = 'a' * _n
        _dumped = serf.get_request_class('event', ).dumps(
                _request.command,
                0,
                _body_without_payload,
            )
        _n += 1

    _body_overlimit = _body_without_payload.copy()
    _body_overlimit['Payload'] = 'a' * (_n + 1)

    _request = serf.get_request_class('event')(**_body_overlimit)

    with pytest.raises(serf.InvalidRequest) :
        _request.check(None, )

    _body_overlimit['Payload'] = 'a' * (_n - 1)

    _request = serf.get_request_class('event')(**_body_overlimit)

    _request.check(None, )

    assert _request.is_checked


def test_request_stop () :
    _request = serf.get_request_class('stop')(Stop=10, )
    _request.check(None, )

    assert _request.is_checked

    # not int argument
    _request = serf.get_request_class('stop')(Stop='no-int', )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked




