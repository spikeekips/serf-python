import pytest
import serf

from _base import FakeClient, FakeConnection

def test_request_join () :
    _body = dict(
            Existing=('127.0.0.1:7901', ),
            Replay=True,
        )
    _request = serf.get_request_class('join')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict( # missing value
            What='is it',
        )

    _request = serf.get_request_class('join')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict(
            Existing=('127.0.0.1:7901', ),
            Replay=1, # invalid value, it must be bool
        )

    _request = serf.get_request_class('join')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


class JoinFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01\x81\xa3Num\x01',
        )


def test_response_join () :
    _client = serf.Client(connection_class=JoinFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'join'
        assert not response.error
        assert response.is_success
        assert response.body is not None
        assert response.seq == 1

        _body = response.body

        assert isinstance(_body, dict, )
        assert 'Num' in _body
        assert _body.get('Num') == 1


    _body = dict(
            Existing=('127.0.0.1:7901', ),
            Replay=True,
        )
    _client.join(**_body).add_callback(_callback, ).request()


