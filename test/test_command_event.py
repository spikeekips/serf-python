import serf
import pytest


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



