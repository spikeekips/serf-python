import threading

from . import _exceptions


# TODO: hold to run `MembersWatcher`, because the current implementation of
# `members` command of `serf` does not return the `rpc` address.
class MembersWatcher (threading.Thread, ) :
    """
        Usage :

            self._watcher = MembersWatcher(self, )
            self._watcher.setDaemon(True, )
            self._watcher.start()
    """
    _refresh_interval = 5

    def __init__ (self, client, ) :
        threading.Thread.__init__(self)
        self.setName('serf_client_members_watcher', )

        self.started = False
        self.stopped = False

        self.timer = threading.Event()

        self._client = client

    def start (self, ) :
        self.started = True
        super(MembersWatcher, self).start()

        return

    def shutdown (self, dummy=None, ) :
        self.stopped = True
        self.timer.set()

        return

    def run (self, ) :
        self.watch()

        return

    def watch (self, ) :
        while True:
            self.timer.wait(self._refresh_interval, )
            if self.stopped :
                break

            self.timer.clear()

            if self._client._conn.just_connected :
                self._client._request_handshake()

            self._client._request_members(self._callback_members, )

        return

    def _callback_members (self, response, ) :
        if not response.is_success :
            raise _exceptions.RpcError('failed to call `members`, %s.' % response.error, )

        _members = self._client._conn.members[:]
        for i in response.body.get('Members', ) :
            if i.get('Status') not in ('alive', ) :
                continue

            _member = (
                    '.'.join(map(str, i.get('Addr', ), ), ),
                    i.get('Port'),
                )
            if _member in _members :
                continue

            _members.append(_member, )

        self._client._conn.members = _members

        return


