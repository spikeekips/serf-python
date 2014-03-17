import serf
import pytest

from _base import FakeClient


def test_request_leave () :
    _body = dict(
        )

    _request = serf.get_request_class('leave')(**_body)
    _request.check(FakeClient(), )

    assert _request.is_checked

    # `Coalesce` is not bool type
    _body = dict(
            Node='node0', # unknown value
        )

    _request = serf.get_request_class('leave')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


