import serf


class FakeClient (serf.Client, ) :
    ipc_version = serf.constant.DEFAULT_IPC_VERSION


class FakeSocket (object, ) :
    def __init__ (self, ) :
        self.data_sent = list()
        self.data_received = list()

    def connect (self, *a, **kw) :
        return 

    def settimeout (self, *a, **kw) :
        return

    def sendall (self, data, ) :
        self.data_sent.append(data, )
        return

    def recv (self, buflen, ) :
        if not self.data_received :
            return ''

        return self.data_received.pop(0, )


class FakeConnection (serf.Connection, ) :
    socket_data = list()

    def __init__ (self, *a, **kw) :
        super(FakeConnection, self).__init__(*a, **kw)

        self._data = list()

    def _connect_node (self, host, port, **queries) :
        _socket = FakeSocket()
        if self.socket_data :
            _socket.data_received.extend(list(self.socket_data), )

        return _socket

    def disconnect (self, ) :
        self._conn = None

        return super(FakeConnection, self).disconnect()


