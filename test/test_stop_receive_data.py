import serf
import msgpack

from _base import FakeConnection

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


def test_response_stream_stop_receive_data () :
    _client = serf.Client(connection_class=StreamFakeConnection, )

    _responses = list()

    def _callback (response, ) :
        assert response.request.command == 'stream'
        assert not response.error
        assert response.is_success
        assert response.body is not None
        assert response.seq == 1

        assert response.body.get('LTime') in StreamFakeConnection.events

        if response.body.get('LTime') in (7, ) :
            raise _exceptions.StopReceiveData

        _responses.append(response, )

        return

    _body = dict(
            Type='*',
        )

    _client.stream(**_body).add_callback(_callback, ).watch()
    assert len(_responses) == 2

    _event_ids = StreamFakeConnection.events.keys()
    _event_ids.sort()

    for _n, i in enumerate(_event_ids[:len(_responses)]) :
        assert _responses[_n].body == StreamFakeConnection.events[i]

    return


