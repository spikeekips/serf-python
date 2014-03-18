import serf
from _base import FakeConnection


class HandshakeFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
        )


def test_support_context_manager () :
    _client = serf.Client(connection_class=HandshakeFakeConnection, )
    with _client :
        assert not _client._conn.disconnected

        _client.handshake()
        _client.request()

    assert _client._conn.disconnected


