import socket
import time
import logging

from . import _exceptions
from . import constant


log = logging.getLogger('serf-rpc-client', )


class Connection (object, ) :
    def connection_disconnected (func, ) :
        def w (self, *a, **kw) :
            try :
                return func(self, *a, **kw)
            except _exceptions.ConnectionLost, e :
                self._conn = None
                self.just_connected = False

                raise e

        return w

    def __init__ (self, hosts=None, timeout=constant.DEFAULT_TIMEOUT, auto_reconnect=False, ) :
        assert type(hosts) in (list, tuple, )

        log.debug('will connect to %s' % hosts, )

        self._all_members = list()
        self.members = hosts[:]
        self._timeout = timeout
        self._auto_reconnect = auto_reconnect

        self._conn = None
        self._once_connected = False
        self.just_connected = False
        self.disconnected = True

    def __del__ (self, ) :
        try :
            self.disconnect()
        except :
            pass

    def _get_members (self, ) :
        return self._members

    def _set_members (self, m, ) :
        self._members = m
        for i in self._members :
            if i in self._all_members :
                continue

            self._all_members.append(i, )

    def _get_timeout (self, ) :
        return self._timeout

    members = property(_get_members, _set_members,)

    @connection_disconnected
    def _set_timeout (self, t, ) :
        self._timeout = t
        #self.connection.settimeout(float(self._timeout) if self._timeout else None, )

        return

    timeout = property(_get_timeout, _set_timeout, )

    @property
    def connection (self, ) :
        if self._conn :
            return self._conn

        if self._once_connected and self.disconnected :
            raise _exceptions.Disconnected

        if not self.members :
            raise _exceptions.ConnectionError('no members to connect', )

        _members = self.members[:]
        _sock = self._connection(_members, )

        if _sock is None and self._once_connected :
            if self._auto_reconnect :
                _members = self._all_members[:]
                _n = 0
                while True :
                    if _n >= constant.CONNECTION_RETRY :
                        break

                    _sleep = constant.CONNECTION_RETRY_INTERVAL * (_n + 1)
                    log.debug('failed to connect, will retry after %d seconds.' % _sleep, )
                    time.sleep(_sleep, )

                    _sock = self._connection(_members, )
                    _n += 1

        if _sock is None :
            raise _exceptions.ConnectionError(
                        'tried to all the known members, but failed, %s' % _members, )

        if not self.just_connected :
            self.just_connected = True

        if not self._once_connected :
            self._once_connected = True

        self.disconnected = False
        self._conn = _sock
        return self._conn

    def _connection (self, members, ) :
        if not members :
            raise _exceptions.ConnectionError('no members to connect', )

        _sock = None
        _members = members[:]
        for _host in _members :
            try :
                _sock = self._connect_node(*_host)
            except _exceptions.ConnectionError, e :
                try :
                    self.members.remove(_host, )
                except ValueError :
                    pass

                log.error(e, )
                continue
            else :
                break

        return _sock

    def _connect_node (self, host, port, ) :
        log.debug('trying to connect to %s:%d' % (host, port, ), )

        _sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _sock.settimeout(self.timeout, )

        try :
            _sock.connect((host, port, ), )
        except (socket.timeout, socket.error, ), e :
            raise _exceptions.ConnectionError('%s (%s:%d)' % (e, host, port, ), )

        log.debug('connected to %s:%d' % (host, port, ), )

        return _sock

    def connect (self, ) :
        self.disconnected = False
        return self.connection

    def disconnect (self, ) :
        self.disconnected = True
        if self._conn is None :
            return

        _host, _port = self._conn.getpeername()
        log.debug('trying to disconnect connection of %s:%d' % (_host, _port, ), )

        try :
            self._conn.close()
        except socket.error :
            pass

        self._conn = None

        return

    @connection_disconnected
    def write (self, request, ) :
        _data = str(request, )

        log.debug('trying to request command: %s' % (repr(request), ), )

        _n = 0
        while True :
            if _n > constant.WRITE_RETRY :
                raise _exceptions.ConnectionLost('failed to write.', )

            try :
                self.connection.sendall(_data, )
            except (socket.error, socket.timeout, ) :
                _n += 1
            else :
                break

        self.just_connected = False
        log.debug('> send data: %s' % ((_data, ), ), )

        return

    @connection_disconnected
    def read (self, buflen=constant.DEFAULT_READ_BUFFER_SIZE, timeout=constant.DEFAULT_TIMEOUT, ) :
        assert constant.DEFAULT_READ_BUFFER_SIZE > 10
        assert timeout is None or timeout > 0

        self.timeout = timeout
        try :
            self.connection.settimeout(float(self.timeout) if self.timeout else None, )
            _data = self.connection.recv(buflen, )
            if not _data :
                raise
        except :
            if self.disconnected :
                raise _exceptions.Disconnected('disconnected', )

            raise _exceptions.ConnectionLost()

        return _data


