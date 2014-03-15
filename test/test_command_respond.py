import serf
import pytest


class FakeClient (object, ) :
    seq = 100


def test_request_respond () :
    _body = dict(
            ID=10,
            Payload='payload',
        )

    _request = serf.get_request_class('respond')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict(
            ID='not-int',
            Payload='payload',
        )

    _request = serf.get_request_class('respond')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


def test_request_respond_payload_size_limit () :
    _body_normal = dict(
            ID=10,
            Payload='a',
        )
    _request = serf.get_request_class('respond')(**_body_normal)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _dumped = ''

    _n = 10
    _body_without_payload = dict(ID=10, Payload='', )
    while len(str(_dumped)) < serf.constant.RESPOND_PAYLOAD_SIZE_LIMIT :
        _body_without_payload['Payload'] = 'a' * _n
        _dumped = serf.get_request_class('respond', ).dumps(
                _request.command,
                FakeClient.seq,
                _body_without_payload,
            )
        _n += 1

    _body_overlimit = _body_without_payload.copy()
    _body_overlimit['Payload'] = 'a' * (_n + 1)

    _request = serf.get_request_class('respond')(**_body_overlimit)

    with pytest.raises(serf.InvalidRequest) :
        _request.check(FakeClient(), )

    _body_overlimit['Payload'] = 'a' * (_n - 1)

    _request = serf.get_request_class('respond')(**_body_overlimit)

    _request.check(FakeClient(), )

    assert _request.is_checked


