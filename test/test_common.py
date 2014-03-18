import serf

from _base import FakeConnection


# basic test

## parsing hosts 

def test_hosts_argument () :
    _hosts_parsed = [('127.0.0.1', 7373, ), ('192.168.0.22', 7300, ), ]
    _hosts = ','.join(map(lambda x : ':'.join(map(str, x, ), ), _hosts_parsed, ), )

    _client = serf.Client(hosts=_hosts, )
    assert map(lambda x : x[:2], _client._conn._members) == _hosts_parsed


def test_hosts_argument_missing_port () :
    _hosts_parsed = [('127.0.0.1', ), ('192.168.0.22', ), ]
    _hosts = ','.join(map(lambda x : ':'.join(map(str, x, ), ), _hosts_parsed, ), )

    _client = serf.Client(hosts=_hosts, )
    for n, i in enumerate(_client._conn._members, ) :
        assert i[0] == _hosts_parsed[n][0]
        assert i[1] == serf.constant.DEFAULT_PORT


def test_hosts_argument_simple () :
    _host = ('192.168.100.1', 7374, )
    _client = serf.Client('%s:%s' % _host, )

    assert len(_client._conn._members) == 1
    assert _client._conn._members[0][:2] == _host


def test_hosts_argument_url_format () :
    _host = ('serf', '192.168.100.1', 7374, )
    _client = serf.Client('%s://%s:%s' % _host, )

    assert len(_client._conn._members) == 1
    assert _client._conn._members[0][:2] == _host[1:]


def test_hosts_argument_with_auth_token () :
    _host = 'serf://192.168.100.1:7374?AuthKey=this-is-token,serf://192.168.100.2:7373?AuthKey=this-is-another-token'

    _client = serf.Client(_host, )
    assert 'AuthKey' in _client._conn._members[0][2]
    assert _client._conn._members[0][2]['AuthKey'] == 'this-is-token'

    assert 'AuthKey' in _client._conn._members[1][2]
    assert _client._conn._members[1][2]['AuthKey'] == 'this-is-another-token'


def test_default_hosts () :
    _client = serf.Client()

    assert _client._conn._members == [
            (serf.constant.DEFAULT_HOST, serf.constant.DEFAULT_PORT, dict(), ), ]


def test_initial_seq () :
    _client = serf.Client()

    assert _client.seq == 0


class JoinFakeConnectionNormal (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01\x81\xa3Num\x01',
        )


class JoinFakeConnectionMangled (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01\x82\xa5Error\xa0\xa3Seq\x01\x81\xa3Num\x01',
        )


def test_response_join () :
    def _callback (response, ) :
        assert response.request.command == 'join'
        assert not response.error
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
    _client = serf.Client(connection_class=JoinFakeConnectionNormal, )
    _client.join(**_body).add_callback(_callback, ).request()

    _client = serf.Client(connection_class=JoinFakeConnectionMangled, )
    _client.join(**_body).add_callback(_callback, ).request()


class JoinFakeConnectionGotError (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xb7Authentication required\xa3Seq\x01',
            '\x82\xa5Error\xb7Authentication required\xa3Seq\x01',
        )


def test_got_error () :
    def _callback (response, ) :
        assert response.request.command == 'join'
        assert response.error
        assert not response.is_success
        assert response.body is None
        assert response.seq == 1

    _body = dict(
            Existing=('127.0.0.1:7901', ),
            Replay=True,
        )
    _client = serf.Client(connection_class=JoinFakeConnectionGotError, )
    _client.join(**_body).add_callback(_callback, ).request()



