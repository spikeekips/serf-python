import serf
import pytest


def test_request_stop () :
    _request = serf.get_request_class('stop')(Stop=10, )
    _request.check(None, )

    assert _request.is_checked

    # not int argument
    _request = serf.get_request_class('stop')(Stop='no-int', )
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(None, )

    assert not _request.is_checked




