import serf
import pytest

from _base import FakeClient, FakeConnection


def test_request_event () :
    _body = dict(
            Name='anonymous-event',
            Payload='payload',
        )

    _request = serf.get_request_class('event')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict(
            Name='anonymous-event',
            Payload='payload',
            Coalesce=1, # `Coalesce` is not bool type
        )

    _request = serf.get_request_class('event')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict( # empty values
        )

    _request = serf.get_request_class('event')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


def test_request_event_payload_size_limit () :
    _body_normal = dict(
            Name='anonymous-event',
            Payload='payload',
        )
    _request = serf.get_request_class('event')(**_body_normal)
    _request.check(FakeClient(), )

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
        _request.check(FakeClient(), )

    _body_overlimit['Payload'] = 'a' * (_n - 1)

    _request = serf.get_request_class('event')(**_body_overlimit)

    _request.check(FakeClient(), )

    assert _request.is_checked


class EventFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01',
        )


def test_response_event () :
    _client = serf.Client(connection_class=EventFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'event'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 1


    _body = dict(
            Name='anonymous-event',
            Payload='payload',
        )

    _client.event(**_body).add_callback(_callback, ).request()


