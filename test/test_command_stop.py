import serf
import pytest

from _base import FakeClient


def test_request_stop () :
    _body = dict(
            Stop=10,
        )

    _request = serf.get_request_class('stop')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict( # unknown values
            Name='anonymous-stop',
            Payload='payload',
            Coalesce=1,
        )

    _request = serf.get_request_class('stop')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked

    _body = dict( # empty values
        )

    _request = serf.get_request_class('stop')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


