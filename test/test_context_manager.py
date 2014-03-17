from _base import FakeClient, FakeConnection


class FakeClient (FakeClient, ) :
    is_connected = False
    is_disconnected = False

    @property
    def is_connected (self, ) :
        return bool(self._conn.connection)

    def disconnect (self, *a, **kw) :
        self._conn.connection = False
        self.is_disconnected = True

        return


class FakeConnection (FakeConnection, ) :
    connection = True

    def connect (self, *a, **kw) :
        pass

    def disconnect (self, *a, **kw) :
        pass


def test_support_context_manager () :
    _client = FakeClient(connection_class=FakeConnection, )
    with _client :
        assert _client.is_connected
        assert not _client.is_disconnected

        _client.handshake()
        _client.request()

    assert not _client.is_connected
    assert _client.is_disconnected


