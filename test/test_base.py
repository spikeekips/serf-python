import serf

from _base import FakeConnection, FakeSocket


def test_fake_connection () :
    _client = serf.Client(connection_class=FakeConnection, )
    assert _client._conn.connection is not None
    assert not _client._conn.disconnected

    assert isinstance(_client._conn.connection, FakeSocket, )


