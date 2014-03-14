import serf


class FakeClient :
    ipc_version = serf.constant.DEFAULT_IPC_VERSION


def test_request_handshake () :
    _request = serf.get_request_class('handshake')()
    _request.check(FakeClient, )

    assert _request.is_checked
    assert 'Version' in _request.body
    assert _request.body.get('Version') == FakeClient.ipc_version



