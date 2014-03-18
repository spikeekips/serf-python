import serf
import uuid

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
            '\x82\xa5Error\xa0\xa3Seq\x01',
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


def test_response_bad_handshake_request () :
    _client = serf.Client(connection_class=HandshakeFakeConnection, )
    assert not _client.is_handshaked

    def _callback (response, ) :
        assert response.request.command == 'handshake'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 0

    _client.force_leave(Node='unknown-node0', ).handshake().add_callback(_callback, ).request()

    assert _client.is_handshaked


def test_response_handshake_default_callback () :
    _client = serf.Client(connection_class=HandshakeFakeConnection, )
    assert not _client.is_handshaked

    def _callback (response, ) :
        assert response.request.command == 'handshake'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 0

    _client.handshake().add_callback(_callback, ).force_leave(Node='unknown-node0', ).request()

    assert _client.is_handshaked


class HandshakeFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01',
        )


def test_response_handshake_and_auth () :
    _auth_key = uuid.uuid1().hex
    _host = 'serf://127.0.0.1:7373?AuthKey=%s' % _auth_key
    _client = serf.Client(_host, connection_class=HandshakeFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'handshake'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 0

    _client.handshake().add_callback(_callback, ).request()


