import pytest
import serf

from _base import FakeClient, FakeConnection

def test_request_members () :
    _request = serf.get_request_class('members')()
    _request.check(FakeClient(), )

    assert _request.is_checked

    _body = dict(
            What='is it',
        )

    _request = serf.get_request_class('members')(**_body)
    with pytest.raises(serf.InvalidRequest, ) :
        _request.check(FakeClient(), )

    assert not _request.is_checked


class MembersFakeConnection (FakeConnection, ) :
    socket_data = (
            '\x82\xa5Error\xa0\xa3Seq\x00',
            '\x82\xa5Error\xa0\xa3Seq\x01\x81\xa7Members\x92\x8b\xa4Addr\x94\x7f\x00\x00\x01\xabDelegateMin\x02\xabProtocolCur\x02\xabProtocolMax\x02\xa4Name\xa5node0\xa6Status\xa5alive\xabDelegateCur\x04\xa4Tags\x81\xa4role\xabtest-server\xabProtocolMin\x01\xa4Port\xcd\x1e\xdc\xabDelegateMax\x04\x8b\xa4Addr\x94\x7f\x00\x00\x01\xabDelegateMin\x02\xabProtocolCur\x02\xabProtocolMax\x02\xa4Name\xa5node1\xa6Status\xa7leaving\xabDelegateCur\x04\xa4Tags\x80\xabProtocolMin\x01\xa4Port\xcd\x1e\xdd\xabDelegateMax\x04',
        )


def test_response_members () :
    _client = serf.Client(connection_class=MembersFakeConnection, )

    def _callback (response, ) :
        assert response.request.command == 'members'
        assert not response.error
        assert response.is_success
        assert response.body is not None
        assert response.seq == 1

        _members = response.body.get('Members', )

        assert 'Members' in response.body
        assert len(_members, ) == 2

        # Addr
        assert _members[0].get('Addr') == [127, 0, 0, 1]
        assert _members[1].get('Addr') == [127, 0, 0, 1]

        # Name
        assert _members[0].get('Name') == 'node0'
        assert _members[1].get('Name') == 'node1'

        # Port
        assert _members[0].get('Port') == 7900
        assert _members[1].get('Port') == 7901

        # Tags
        assert isinstance(_members[0].get('Tags'), dict, )
        assert isinstance(_members[1].get('Tags'), dict, )
        assert _members[0].get('Tags') == {'role': 'test-server'}

        # Status
        assert _members[0].get('Status') == 'alive'
        assert _members[1].get('Status') == 'leaving'


    _client.members().add_callback(_callback, ).request()


