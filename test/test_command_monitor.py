import serf
import pytest
import msgpack

from _base import FakeClient, FakeConnection


def test_request_monitor () :
    _body = dict(
            LogLevel='DEBUG',
        )

    _request = serf.get_request_class('monitor')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict( # missing value
        )

    _request = serf.get_request_class('monitor')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict(
            LogLevel=True, # this must be str
        )

    _request = serf.get_request_class('monitor')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


from serf.connection import when_connection_lost
from serf import _exceptions

class MonitorFakeConnection (FakeConnection, ) :
    logs = (
            {'Log': '2014/03/17 22:23:18 [DEBUG] memberlist: Responding to push/pull sync with: 127.0.0.1:63080'},
            {'Log': '2014/03/17 22:23:18 [DEBUG] memberlist: Initiating push/pull sync with: 127.0.0.1:7901'},
            {'Log': '2014/03/17 22:23:48 [DEBUG] memberlist: Responding to push/pull sync with: 127.0.0.1:63083'},
            {'Log': '2014/03/17 22:24:18 [DEBUG] memberlist: Responding to push/pull sync with: 127.0.0.1:63084'},
            {'Log': '2014/03/17 22:24:18 [DEBUG] memberlist: Initiating push/pull sync with: 127.0.0.1:7901'},
            {'Log': '2014/03/17 22:24:48 [DEBUG] memberlist: Responding to push/pull sync with: 127.0.0.1:63086'},
            {'Log': '2014/03/17 22:24:48 [DEBUG] memberlist: Initiating push/pull sync with: 127.0.0.1:7901'},
            {'Log': '2014/03/18 00:31:52 [INFO] agent.ipc: Accepted client: 127.0.0.1:64213'},
            {'Log': '2014/03/18 00:32:08 [INFO] agent.ipc: Accepted client: 127.0.0.1:64215'},
        )

    socket_data = [
            '\x82\xa5Error\xa0\xa3Seq\x00', # for handshake
        ]

    for i in logs :
        socket_data.append('\x82\xa5Error\xa0\xa3Seq\x01', )
            
        socket_data.append(msgpack.packb(i), )

    socket_data.append('END', )

    @when_connection_lost
    def read (self, *a, **kw) :
        _data = super(MonitorFakeConnection, self).read(*a, **kw)
        if _data == 'END' :
            raise _exceptions.Disconnected

        return _data


def test_response_monitor () :
    _client = serf.Client(connection_class=MonitorFakeConnection, )

    logs = list(MonitorFakeConnection.logs[:], )

    def _callback (response, ) :
        assert response.request.command == 'monitor'
        assert not response.error
        assert response.is_success
        assert response.body is not None
        assert response.seq == 1

        _log = response.body
        _log_received = logs.pop(0, )
        assert _log == _log_received


    _body = dict(
            LogLevel='DEBUG',
        )

    _client.monitor(**_body).add_callback(_callback, ).watch()


