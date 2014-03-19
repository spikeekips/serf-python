import socket
import urlparse
import urllib
import string
import time
import logging

from . import _exceptions
from . import constant


log = logging.getLogger('serf-rpc-client', )


AVAILABLE_HOST_URI_QUERY_KEYS = set([
        'AuthKey',
    ], )


def parse_host (h, ) :
    _hosts = list()
    for i in filter(string.strip, h.split(','), ) :
        _h = _parse_host(i, )
        if not _h :
            continue

        _hosts.append(tuple(_h, ), )

    return _hosts


def _parse_host (h, ) :
    if not h.startswith('serf://') :
        h = 'serf://%s' % h
    
    _parsed = list(urlparse.urlparse(h, ), )
    if _parsed[0] not in ('serf', ) :
        raise _exceptions.InvalidHostURL('invalid host url, `%s`.' % h, )

    # the `urlparse` module in `travis-cis` does not understand the
    # non-standard scheme like `serf'.
    _parsed[0] = 'http'
    if not _parsed[2].startswith('/') :
        _parsed[2] = '/' + _parsed[2]

    _parsed = urlparse.urlparse(urlparse.urlunparse(_parsed, ), )

    _host = map(
            lambda x : None if x in ('', -1, ) else x,
            urllib.splitnport(_parsed.netloc, defport=7373, ),
        )
    
    if not _host[0] and not _host[1] :
        raise _exceptions.InvalidHostURL('invalid host url, `%s`.' % h, )
    
    if not _host[0] :
        _host[0] = constant.DEFAULT_HOST
    
    if not _host[1] :
        _host[1] = constant.DEFAULT_PORT
    
    _queries = dict()
    if _parsed.query :
        _queries = dict(map(
                urllib.splitvalue,
                filter(string.strip, _parsed.query.split('&'), ),
            ), )
        if set(_queries.keys()) != AVAILABLE_HOST_URI_QUERY_KEYS :
            raise _exceptions.InvalidHostURL(
                    'unknown key found, %s' % list(
                        set(_queries.keys() - AVAILABLE_HOST_URI_QUERY_KEYS), ),
                )
    
    _host.append(_queries, )
    
    return _host


def when_connection_lost (func, ) :
    def w (self, *a, **kw) :
        try :
            return func(self, *a, **kw)
        except _exceptions.Disconnected, e :
            self.run_callback('disconnected', )

            raise e
        except _exceptions.ConnectionLost, e :
            self.run_callback('connection_lost', )

            raise e

    return w


class Connection (object, ) :
    _callbacks = dict(
            connection_lost=list(),
            disconnected=list(),
        )

    def __init__ (self,
                    hosts=None,
                    timeout=constant.DEFAULT_TIMEOUT,
                    auto_reconnect=False,
                    stop_reconnect_nth_failed=constant.CONNECTION_RETRY,
                ) :
        assert type(hosts) in (list, tuple, )

        log.info('will connect to %s' % hosts, )

        self.members = hosts[:]
        self._timeout = timeout
        self._auto_reconnect = auto_reconnect
        self._stop_reconnect_nth_failed = stop_reconnect_nth_failed

        self.current_member = None
        self._conn = None
        self._once_connected = False
        self.disconnected = True

        self._callbacks = self.__class__._callbacks.copy()
        self.add_callback(connection_lost=self._callback_connection_lost, )
        self.add_callback(disconnected=self._callback_disconnected, )


    def _callback_connection_lost (self, *a, **kw) :
        self._conn = None

        return

    def _callback_disconnected (self, *a, **kw) :
        return

    def add_callback (self, **callbacks) :
        for k, v in callbacks.items() :
            if k not in self._callbacks :
                continue

            if type(v) not in (list, tuple, ) :
                v = [v, ]

            self._callbacks[k].extend(v, )

        return

    def run_callback (self, type, ) :
        for i in self._callbacks.get(type, ) :
            i(self, )

        return

    def __del__ (self, ) :
        try :
            self.disconnect()
        except :
            pass

    def _get_members (self, ) :
        return self._members

    def _set_members (self, m, ) :
        self._members = m

    def _get_timeout (self, ) :
        return self._timeout

    members = property(_get_members, _set_members,)

    @when_connection_lost
    def _set_timeout (self, t, ) :
        self._timeout = t

        return

    timeout = property(_get_timeout, _set_timeout, )

    @property
    @when_connection_lost
    def connection (self, ) :
        if self._conn :
            return self._conn

        if self._once_connected and self.disconnected :
            raise _exceptions.Disconnected

        if not self.members :
            raise _exceptions.ConnectionError('no members to connect', )

        _members = self.members[:]
        _sock = self._connection(self.members, )

        if _sock is None and self._once_connected and self._auto_reconnect :
            _n = 0

            if self._stop_reconnect_nth_failed :
                _wait_until = lambda x : x < self._stop_reconnect_nth_failed
            else :
                _wait_until = lambda x : True

            while _wait_until(_n, ):
                _sleep = constant.CONNECTION_RETRY_INTERVAL * (_n + 1)
                log.info('failed to connect, will retry after %d seconds.' % _sleep, )
                time.sleep(_sleep, )

                _sock = self._connection(_members, )
                if _sock :
                    break

                if _n < 5 :
                    _n += 1

        if _sock is None :
            raise _exceptions.ConnectionError(
                        'tried to all the known members, but failed, %s' % _members, )

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
                _sock = self._connect_node(*_host[:2], **_host[2])
                self.current_member = _host
                break
            except _exceptions.ConnectionError, e :
                log.error(e, )

                try :
                    self.members.remove(_host, )
                except ValueError :
                    pass

                self.members.append(_host, )

        return _sock

    def _connect_node (self, host, port, **queries) :
        log.info('trying to connect to %s:%d' % (host, port, ), )

        _sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _sock.settimeout(self.timeout, )

        try :
            _sock.connect((host, port, ), )
        except (socket.timeout, socket.error, ), e :
            raise _exceptions.ConnectionError('%s (%s:%d)' % (e, host, port, ), )

        log.info('connected to %s:%d' % (host, port, ), )

        return _sock

    def connect (self, ) :
        self.disconnected = False
        return self.connection

    def disconnect (self, ) :
        self.run_callback('disconnected', )
        self.disconnected = True
        if self._conn is None :
            return

        _host, _port = self._conn.getpeername()
        log.info('trying to disconnect connection of %s:%d' % (_host, _port, ), )

        try :
            self._conn.close()
        except socket.error :
            pass

        self._conn = None

        return

    @when_connection_lost
    def write (self, data, ) :
        _n = 0
        while True :
            if _n > constant.WRITE_RETRY :
                raise _exceptions.ConnectionLost('failed to write.', )

            try :
                self.connection.sendall(data, )
            except (socket.error, socket.timeout, ) :
                _n += 1
            else :
                break

        log.debug('> %s' % ((data, ), ), )

        return

    @when_connection_lost
    def read (self, buflen=constant.DEFAULT_READ_BUFFER_SIZE, timeout=constant.DEFAULT_TIMEOUT, ) :
        assert constant.DEFAULT_READ_BUFFER_SIZE > 10
        assert timeout is None or timeout > 0

        self.timeout = timeout
        try :
            self.connection.settimeout(float(self.timeout) if self.timeout else None, )
            _data = self.connection.recv(buflen, )
            log.debug('< %s' % ((_data, ), ), )
            if not _data :
                raise
        except KeyboardInterrupt :
            raise
        except socket.timeout, e :
            raise _exceptions.Disconnected(e, )
        except :
            if self.disconnected :
                raise _exceptions.Disconnected('disconnected', )

            raise _exceptions.ConnectionLost()

        return _data


