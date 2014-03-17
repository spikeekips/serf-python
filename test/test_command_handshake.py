import serf

from _base import FakeConnection, FakeClient


def test_request_handshake () :
    _request = serf.get_request_class('handshake')()
    _request.check(FakeClient(), )

    assert _request.is_checked
    assert 'Version' in _request.body
    assert _request.body.get('Version') == FakeClient.ipc_version

    # set by default in Client
    _new_ipc_version = 101
    _request = serf.get_request_class('handshake')()
    _request.check(FakeClient(ipc_version=_new_ipc_version, ), )

    assert _request.is_checked
    assert 'Version' in _request.body
    assert _request.body.get('Version') == _new_ipc_version

    # set in request body
    _new_ipc_version = 99
    _request = serf.get_request_class('handshake')(Version=_new_ipc_version, )
    _request.check(FakeClient(), )

    assert _request.is_checked
    assert 'Version' in _request.body
    assert _request.body.get('Version') == _new_ipc_version


class HandshakeFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
        )


def test_response_handshake () :
    _client = serf.Client(connection_class=HandshakeFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'handshake'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 0

    _client.handshake().add_callback(_callback, ).request()


