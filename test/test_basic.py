import serf


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



