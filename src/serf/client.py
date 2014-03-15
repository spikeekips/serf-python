import logging
import msgpack
import threading
import string
import urllib
import collections

from . import constant
from . import connection
from . import _exceptions
from .request import FunctionCommandCall
from .command_handler import REQUEST_HANDLER, RESPONSE_HANDLER


log = logging.getLogger('serf-rpc-client', )


class Client (threading.local, ) :
    def __init__ (self,
                    hosts=None,
                    ipc_version=constant.DEFAULT_IPC_VERSION,
                    auto_reconnect=False,
                    connection_class=None,
                ) :
        _hosts = list()
        if not hosts :
            _hosts = [(constant.DEFAULT_HOST, constant.DEFAULT_PORT, ), ]
        else :
            for i in filter(string.strip, hosts.split(','), ) :
                _host = map(
                        lambda x : None if x in ('', -1, ) else x,
                        urllib.splitnport(i, defport=7373, ),
                    )
                if not _host[0] and not _host[1] :
                    continue

                if not _host[0] :
                    _host[0] = constant.DEFAULT_HOST

                if not _host[1] :
                    _host[1] = constant.DEFAULT_PORT

                if _host in _hosts :
                    continue

                _hosts.append(tuple(_host, ), )

            if not _hosts :
                raise ValueError('no `hosts` found.', )

        if connection_class is None :
            connection_class = connection.Connection

        self._conn = connection_class(_hosts, auto_reconnect=auto_reconnect, )
        self._conn.add_callback(connection_lost=self._callback_lost_connection, )
        self._conn.add_callback(disconnected=self._callback_disconnected, )

        self.ipc_version = ipc_version

        # assign command handlers
        for i in REQUEST_HANDLER.keys() :
            setattr(self, i, FunctionCommandCall(i, self, ), )

        # initialize state
        self._initialize()

    def _initialize (self, ) :
        self.seq = 0
        self._request_handlers = dict()
        self._received_headers = collections.OrderedDict()
        self._requests_sequence = list()
        self._unpacker = msgpack.Unpacker(use_list=True, )

        return

    def __enter__ (self, ) :
        self.connect()

        return self

    def __exit__(self, exc_type, exc_value, traceback, ) :
        self.disconnect()

        return

    def _callback_lost_connection (self, connection, ) :
        self.seq = 0
        self._request_handlers = dict()
        self._received_headers.clear()

        self._unpacker = msgpack.Unpacker(use_list=True, )

        return

    def _callback_disconnected (self, connection, ) :
        self._initialize()

        return

    def connect (self, ) :
        self._conn.connect()

        return self

    def disconnect (self, wait=False, ) :
        if wait and len(self._requests_sequence) > 0 :
            self._append_callback(lambda x : self.disconnect(), )

            return self

        self._conn.disconnect()

        return

    def _get_request_class (self, command, ) :
        return REQUEST_HANDLER.get(command, )

    def add_callback (self, *callbacks) :
        self._append_callback(*callbacks)
        return self

    def _append_callback (self, *callbacks) :
        assert len(self._requests_sequence) > 0

        self._requests_sequence[-1].add_callback(*callbacks)

        return

    def _callback_handshake (self, response, ) :
        if not response.is_success :
            raise _exceptions.RpcError('failed to call `handshake`, %s.' % response.error, )

        log.debug('successfully handshaked', )

        return

    def _request_handshake (self, ) :
        _request = self._get_request_class('handshake', )(
                Version=self.ipc_version,
            ).check(self, ).add_callback(self._callback_handshake, )

        self._request(_request, )
        return self._get_response().callback().is_success

    def request_by_request (self, request, ) :
        # remove the duplicated command, unperiodically `serf` rpc server miss
        # the some responses.
        _callbacks = list()
        for _n, i in enumerate(self._requests_sequence) :
            if i.command == request.command :
                _callbacks.extend(self._requests_sequence[_n].callbacks, )
                del self._requests_sequence[_n]

        # restore the callbacks, already connected.
        if _callbacks :
            request.callbacks.extend(_callbacks, )

        self._requests_sequence.append(request, )

        return self

    def request (self, watch=False, timeout=constant.DEFAULT_TIMEOUT, requests=None, ) :
        if not self._requests_sequence and not requests :
            raise _exceptions.RpcError('no requests registered.', )

        if requests :
            _requests = requests
        else :
            _requests = self._requests_sequence[:]
            self._requests_sequence = list()

        _missing_handshake = _requests[0].command != 'handshake'

        _stream_requests = list()

        _requests_sequence =  _requests[:]
        for i in _requests_sequence :
            # check whether the connection is still available or not.
            self._conn.connection

            if not self._conn.just_connected and i.command == 'handshake' :
                _requests.remove(i, )
                continue

            if self._conn.just_connected and _missing_handshake :
                self._request_handshake()

            if watch and i.need_watchful :
                _stream_requests.append(i, )

            if i.force_watchful :
                if i not in _stream_requests :
                    _stream_requests.append(i, )

                watch = True

            self._request(i, )

        self._unpacker = msgpack.Unpacker(use_list=True, )

        _responses = self._handle_response(
                _requests,
                _stream_requests,
                timeout=timeout,
                watch=watch,
            )

        return _responses

    def watch (self, timeout=None, ) :
        return self.request(watch=True, timeout=timeout, )

    def _handle_response (self, requests, stream_requests=None, timeout=None, watch=False, ) :
        if stream_requests :
            timeout = None

        _requests = requests[:]
        _responses = list()
        while True :
            if not stream_requests and not _requests :
                break

            try :
                _response = self._get_response(timeout=timeout, )
            except _exceptions.ConnectionLost :
                log.debug('connection lost.', )

                return self.request(
                        watch=watch,
                        requests=_requests,
                    )
            except _exceptions.Disconnected :
                log.debug('disconnected', )
                return _responses

            _response_callbacked =_response.callback()
            if _response_callbacked :
                _responses.append(_response, )

            if not _response.has_more_responses :
                if _response.request in _requests :
                    _requests.remove(_response.request, )

                del self._request_handlers[_response.seq]

                if _response.seq in self._received_headers :
                    del self._received_headers[_response.seq]

                if _response.request in stream_requests :
                    stream_requests.remove(_response.request, )

        return _responses

    def _request (self, request, ) :
        request.seq = self.seq
        self._request_handlers[self.seq] = request
        self.seq += 1

        log.debug('trying to request command: %s' % (repr(request), ), )

        self._conn.write(str(request, ), )
        return

    def _handle_header (self, parsed, ) :
        if 'Seq' not in parsed or 'Error' not in parsed :
            raise _exceptions.ThisIsNotHeader

        if parsed.get('Seq') not in self._request_handlers :
            raise _exceptions.ThisIsNotValieHeader

        _request = self._request_handlers.get(parsed.get('Seq'), )

        if parsed.get('Seq') in self._received_headers :
            self._received_headers.popitem(parsed.get('Seq'), )

        _response_class = RESPONSE_HANDLER.get(_request.command, )

        self._received_headers[parsed.get('Seq')] = _response_class(
                _request,
                parsed,
                None,
            )

        return _response_class

    def _get_response (self, timeout=None, ) :
        _data = ''

        _body = None
        while True :
            try :
                _parsed = self._unpacker.next()
                try :
                    _response = self._handle_header(_parsed, )
                    if not _response.has_body :
                        break
                except _exceptions.ThisIsNotHeader :
                    _body = _parsed
                    break
                except _exceptions.ThisIsNotValieHeader :
                    continue
            except StopIteration :
                _data = self._conn.read(timeout=timeout, )
                self._unpacker.feed(_data)

        _response = self._received_headers.values()[-1]
        self._received_headers.popitem()

        _response.body = _body
        return _response


