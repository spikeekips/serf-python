import logging
import msgpack
import threading
import string
import urlparse
import urllib

try :
    from collections import OrderedDict
except ImportError :
    from ordereddict import OrderedDict  # for python2.6

from . import constant
from . import connection
from . import _exceptions
from .request import FunctionCommandCall
from .command_handler import REQUEST_HANDLER, RESPONSE_HANDLER


log = logging.getLogger('serf-rpc-client', )


def get_request_class (command, ) :
    return REQUEST_HANDLER.get(command, )


class Client (threading.local, ) :
    def __init__ (self,
                    hosts=None,
                    ipc_version=constant.DEFAULT_IPC_VERSION,
                    auto_reconnect=False,
                    connection_class=None,
                    stop_reconnect_nth_failed=constant.CONNECTION_RETRY,
                ) :
        _hosts = list()
        if not hosts :
            _hosts = [(constant.DEFAULT_HOST, constant.DEFAULT_PORT, dict(), ), ]
        else :
            _hosts = connection.parse_host(hosts, )

            if not _hosts :
                raise ValueError('no `hosts` found.', )

        if connection_class is None :
            connection_class = connection.Connection

        self._conn = connection_class(
                _hosts,
                auto_reconnect=auto_reconnect,
                stop_reconnect_nth_failed=stop_reconnect_nth_failed,
            )
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
        self.is_handshaked = False
        self.is_authed = False
        self._request_handlers = dict()
        self._received_headers = OrderedDict()
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
        self.is_handshaked = False
        self.is_authed = False
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
        return get_request_class(command, )

    def add_callback (self, *callbacks) :
        self._append_callback(*callbacks)
        return self

    def _append_callback (self, *callbacks) :
        assert len(self._requests_sequence) > 0

        self._requests_sequence[-1].add_callback(*callbacks)

        return

    def _callback_handshake (self, response, ) :
        self.is_handshaked = response.is_success

        if not response.is_success :
            log.warning(response.error, )
        else :
            log.info('successfully handshaked', )

        return

    def _callback_auth (self, response, ) :
        self.is_authed = response.is_success

        if not response.is_success :
            raise _exceptions.AuthenticationError(
                    'failed to authed, %s.' % (self._conn.current_member, ),
                )

        log.info('successfully authed', )

        return

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

        _requests = self._check_request_handshake(_requests, )
        _requests = self._check_request_auth(_requests, )

        _stream_requests = list()
        _requests_sequence =  _requests[:]
        for i in _requests_sequence :
            # check whether the connection is still available or not.
            self._conn.connection

            if watch and i.need_watching :
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

    def _check_request_handshake (self, requests, ) :
        if self.is_handshaked :
            return requests

        if requests[0].command == 'handshake' :
            if self._callback_handshake not in requests[0].callbacks :
                requests[0].add_callback(self._callback_handshake, pos=0, )

            return requests

        _request = self._get_request_class('handshake', )(
                Version=self.ipc_version,
            ).check(self, ).add_callback(self._callback_handshake, )
        requests.insert(0, _request, )

        return requests

    def _check_request_auth (self, requests, ) :
        if self.is_authed :
            return requests

        self._conn.connection

        # found auth command in requests
        if bool(filter(lambda x : x.command == 'auth', requests, ), ) :
            for i in requests :
                if i.command != 'auth' :
                    continue

                if self._callback_auth not in i.callbacks :
                    i.add_callback(self._callback_auth, pos=0, )

            return requests

        if 'AuthKey' in self._conn.current_member[2] :
            _request = self._get_request_class('auth', )(
                    AuthKey=self._conn.current_member[2].get('AuthKey'),
                ).check(self, ).add_callback(self._callback_auth, )

            requests.insert(
                    1 if requests[0].command == 'handshake' else 0,
                    _request,
                )

        return requests

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
                log.info('connection lost.', )

                return self.request(
                        watch=watch,
                        requests=_requests,
                    )
            except _exceptions.Disconnected, e :
                log.info('disconnected: %s' % e, )
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

        log.info('trying to request command: %s' % (repr(request), ), )

        self._conn.write(str(request, ), )
        return

    def _handle_header (self, parsed, ) :
        if 'Seq' not in parsed or 'Error' not in parsed :
            raise _exceptions.ThisIsNotHeader

        if parsed.get('Seq') not in self._request_handlers :
            raise _exceptions.ThisIsNotValidHeader

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
                    if _parsed.get('Error', ) or not _response.has_body :
                        break
                except _exceptions.ThisIsNotHeader :
                    _body = _parsed
                    break
                except _exceptions.ThisIsNotValidHeader :
                    continue
            except StopIteration :
                _data = self._conn.read(timeout=timeout, )
                self._unpacker.feed(_data)

        _response = self._received_headers.values()[-1]
        self._received_headers.popitem()

        _response.body = _body
        return _response


