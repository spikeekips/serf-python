import serf
import pytest
import msgpack

from _base import FakeClient, FakeConnection


def test_request_stream () :
    _body = dict(
            Type='*'
        )

    _request = serf.get_request_class('stream')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict( # missing value
        )

    _request = serf.get_request_class('stream')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict(
            Type=True, # this must be str
        )

    _request = serf.get_request_class('stream')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


from serf.connection import when_connection_lost
from serf import _exceptions

class StreamFakeConnection (FakeConnection, ) :
    events = {
            5: {'Coalesce': False, 'LTime': 5, 'Name': 'event-0C46F9B2-C106-4698-AE0C-C3E7C0B603A6', 'Payload': 'Mon Mar 17 22:18:50 KST 2014DD278258-4AEC-4963-B0E1-D025063D22C3', 'Event': 'user'},
            6: {'Coalesce': False, 'LTime': 6, 'Payload': 'Mon Mar 17 22:18:51 KST 2014F13A81A5-2866-48A7-B725-55EF29569E16', 'Event': 'user', 'Name': 'event-AACF3985-22F8-4429-BA2A-B37472896025'},
            7: {'Coalesce': False, 'LTime': 7, 'Payload': 'Mon Mar 17 22:18:51 KST 201493731D44-3CB1-4BDD-8409-BF57012F573F', 'Event': 'user', 'Name': 'event-8F1B6AA1-954E-44E5-B269-A3D8BE6BAFBD'},
        }

    socket_data = [
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01',
        ]

    for k, v in events.items() :
        socket_data.append('\x82\xa5Error\xa0\xa3Seq\x01', )
            
        v['LTime'] = k
        socket_data.append(msgpack.packb(v), )

    socket_data.append('END', )

    @when_connection_lost
    def read (self, *a, **kw) :
        _data = super(StreamFakeConnection, self).read(*a, **kw)
        if _data == 'END' :
            raise _exceptions.Disconnected

        return _data


def test_response_stream () :
    _client = serf.Client(connection_class=StreamFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'stream'
        assert not response.error
        assert response.is_success
        assert response.body is not None
        assert response.seq == 1

        assert response.body.get('LTime') in StreamFakeConnection.events

        _event_received = response.body
        _event_sent = StreamFakeConnection.events.get(_event_received.get('LTime'), )

        assert _event_sent.get('Name')     == _event_received.get('Name')
        assert _event_sent.get('Payload')  == _event_received.get('Payload')
        assert _event_sent.get('Event')    == _event_received.get('Event')


    _body = dict(
            Type='*',
        )

    _client.stream(**_body).add_callback(_callback, ).watch()


