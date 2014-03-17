import serf
import pytest

from _base import FakeClient, FakeConnection


def test_request_force_leave () :
    _body = dict(
            Node='node0',
        )

    _request = serf.get_request_class('force_leave')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    # `Coalesce` is not bool type
    _body = dict(
        )

    _request = serf.get_request_class('force_leave')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


class ForceLeaveFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01',
        )


def test_response_force_leave () :
    _client = serf.Client(connection_class=ForceLeaveFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'force_leave'
        assert not response.error
        assert response.is_success
        assert response.body is None
        assert response.seq == 1


    _body = dict(
            Node='node0',
        )
    _client.force_leave(**_body).add_callback(_callback, ).request()


