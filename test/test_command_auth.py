import serf
import pytest

from _base import FakeClient, FakeConnection


def test_request_auth () :
    _body = dict(
            AuthKey='auth-key',
        )

    _request = serf.get_request_class('auth')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict(
            AuthKey=1, # `AuthKey` must be str
        )

    _request = serf.get_request_class('auth')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict( # empty values
        )

    _request = serf.get_request_class('auth')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked



class AuthFakeConnectionFailed (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xbcInvalid authentication token\xa3Seq\x01',
        )


def test_response_auth_failed () :
    _client = serf.Client(connection_class=AuthFakeConnectionFailed, )

    def _callback (response, ) :
        assert response.request.command == 'auth'
        assert response.error
        assert not response.is_success
        assert response.body is None
        assert response.seq == 1


    _body = dict(
            AuthKey='this-is-bad-authkey',
        )

    assert not _client.is_authed

    with pytest.raises(serf.AuthenticationError, ) :
        _client.auth(**_body).add_callback(_callback, ).request()

    assert not _client.is_authed


class AuthFakeConnectionSuccess (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01',
        )


def test_response_auth_success () :
    _client = serf.Client(connection_class=AuthFakeConnectionSuccess, )

    def _callback (response, ) :
        assert response.request.command == 'auth'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 1


    _body = dict(
            AuthKey='this-is-valid-authkey',
        )

    assert not _client.is_authed

    _client.auth(**_body).add_callback(_callback, ).request()

    assert _client.is_authed


class AuthFakeConnectionForceLeaveSuccess (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01\x82\xa5Error\xa0\xa3Seq\x02',
        )


def test_implicit_authentication_with_host_url_success () :
    def _callback (response, ) :
        assert response.request.command == 'force_leave'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 2


    _body = dict(
            Node='node0',
        )

    _auth_key = 'this-is-valid-authkey'
    _client = serf.Client(
            'serf://127.0.0.1:7373?AuthKey=%s' % _auth_key,
            connection_class=AuthFakeConnectionForceLeaveSuccess,
        )

    assert not _client.is_authed

    _client.force_leave(**_body).add_callback(_callback, ).request()

    assert _client.is_authed


class AuthFakeConnectionForceLeaveFailed (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xbcInvalid authentication token\xa3Seq\x01',
        )


def test_implicit_authentication_with_host_url () :
    def _callback (response, ) :
        assert response.request.command == 'force_leave'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 2


    _body = dict(
            Node='node0',
        )

    _auth_key = 'this-is-valid-authkey'
    _client = serf.Client(
            'serf://127.0.0.1:7373?AuthKey=%s' % _auth_key,
            connection_class=AuthFakeConnectionForceLeaveFailed,
        )

    assert not _client.is_authed

    with pytest.raises(serf.AuthenticationError, ) :
        _client.force_leave(**_body).add_callback(_callback, ).request()

    assert not _client.is_authed


