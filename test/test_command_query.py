import serf
import pytest
import msgpack

from _base import FakeClient, FakeConnection


def test_request_query () :
    _body = dict(
            FilterNodes=["node0", "node1", ],
            FilterTags={"role": ".*"},
            RequestAck=True,
            Timeout=0,
            Name='response-me',
            Payload='this is payload of `response-me` query event',
        )

    _request = serf.get_request_class('query')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict( # missing value
        )

    _request = serf.get_request_class('query')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict(
            Name='response-me',
            Timeout='string',
        )

    _request = serf.get_request_class('query')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


from serf.connection import when_connection_lost
from serf import _exceptions

class QueryFakeConnection (FakeConnection, ) :
    responses = (
                {'Type': 'ack', 'From': 'node0', 'Payload': None},
                {'Type': 'response', 'From': 'node0', 'Payload': 'this is payload of `response-me` query event2014-03-18T00:52:15.993442'},
                {'Type': 'ack', 'From': 'node1', 'Payload': None},
                {'Type': 'done', 'From': '', 'Payload': None},
        )

    socket_data = [
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01',
        ]

    for i in responses :
        socket_data.append('\x82\xa5Error\xa0\xa3Seq\x01', )
        socket_data.append(msgpack.packb(i), )

    socket_data.append('END', )

    @when_connection_lost
    def read (self, *a, **kw) :
        _data = super(QueryFakeConnection, self).read(*a, **kw)
        if _data == 'END' :
            raise _exceptions.Disconnected

        return _data


def test_response_query () :
    _client = serf.Client(connection_class=QueryFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'query'
        assert not response.error
        assert response.is_success
        assert response.body is not None
        assert response.seq == 1

        return


    _body = dict(
            FilterNodes=["node0", "node1", ],
            FilterTags={"role": ".*"},
            RequestAck=True,
            Timeout=0,
            Name='response-me',
            Payload='this is payload of `response-me` query event',
        )

    _responses_all = _client.query(**_body).add_callback(_callback, ).watch()

    _responses = list()
    for i in _responses_all :
        if i.request.command not in ('query', ) :
            continue

        _responses.append(i, )

    for _n, i in enumerate(QueryFakeConnection.responses) :
        assert _responses[_n].body == i


