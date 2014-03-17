import serf

from _base import FakeConnection


# basic test

## parsing hosts 

def test_hosts_argument () :
    _hosts_parsed = [('127.0.0.1', 7373, ), ('192.168.0.22', 7300, ), ]
    _hosts = ','.join(map(lambda x : ':'.join(map(str, x, ), ), _hosts_parsed, ), )

    _client = serf.Client(_hosts, )
    assert _client._conn._members == _hosts_parsed


def test_default_hosts () :
    _client = serf.Client()

    assert _client._conn._members == [
            (serf.constant.DEFAULT_HOST, serf.constant.DEFAULT_PORT, ), ]


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
    _client = serf.Client(connection_class=JoinFakeConnectionNormal, )
    _client.join(**_body).add_callback(_callback, ).request()

    _client = serf.Client(connection_class=JoinFakeConnectionMangled, )
    _client.join(**_body).add_callback(_callback, ).request()


