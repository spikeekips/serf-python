import logging
import msgpack
import threading
import string
import urllib

from . import constant
from . import connection
from . import _exceptions
from .command_handler import REQUEST_HANDLER, RESPONSE_HANDLER


log = logging.getLogger('serf-rpc-client', )


class Client (threading.local, ) :
    def __init__ (self,
                    hosts=None,
                    ipc_version=constant.DEFAULT_IPC_VERSION,
                    auto_reconnect=False,
                ) :
        _hosts = list()
        if not hosts :
            _hosts = ((constant.DEFAULT_HOST, constant.DEFAULT_PORT, ), )
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

        self._conn = connection.Connection(_hosts, auto_reconnect=auto_reconnect, )
        self.ipc_version = ipc_version
        self.seq = 0

        self._initialize()

    def _initialize (self, requests=None, reset_seq=False, ) :
        self._got_first_stream_response = False
        self._command_handlers = dict()

        if reset_seq :
            self.seq = 0

        if requests :
            self._requests_container = requests
        else :
            self._requests_container = list()

        self._unpacker = msgpack.Unpacker(use_list=True, )

    def connect (self, ) :
        self._conn.connect()

        return self

    def disconnect (self, wait=False, ) :
        if wait and len(self._requests_container) > 0 :
            self._append_callback(lambda x : self.disconnect(), )

            return self

        self._conn.disconnect()
        self._watcher.shutdown()

        return

    def __getattr__ (self, command, ) :
        # convert python attribute to the real command
        if command not in constant.COMMAND_LIST :
            return super(Client, self, ).__getattribute__(command, )

        _func = lambda **kw : self.__call__(command, **kw)
        _func.__name__ = command

        return _func

    def __call__ (self, command, **body) :
        _request = REQUEST_HANDLER.get(command, )(**body).check(self, )

        self.request_by_request(_request, )

        return self

    def add_callback (self, *callbacks) :
        self._append_callback(*callbacks)
        return self

    def _append_callback (self, *callbacks) :
        assert len(self._requests_container) > 0

        self._requests_container[-1].add_callback(*callbacks)

        return

    def _callback_handshake (self, response, ) :
        if not response.is_success :
            raise _exceptions.RpcError('failed to call `handshake`, %s.' % response.error, )

        log.debug('successfully handshaked', )

        return

    def _request_handshake (self, ) :
        _request = REQUEST_HANDLER.get('handshake', )(
                Version=self.ipc_version,
            ).check(self, ).add_callback(self._callback_handshake, )

        self._request(_request, )
        return self._get_response().callback().is_success

    def _request_members (self, *callbacks) :
        _request = REQUEST_HANDLER.get('members', )(
            ).check(self, )

        if callbacks is not None :
            _request.add_callback(*callbacks)

        self._request(_request, )
        return self._get_response().callback().is_success

    def request_by_request (self, request, ) :
        # remove the duplicated command, unperiodically `serf` rpc server miss
        # the some responses.
        for _n, i in enumerate(self._requests_container) :
            if i.command == request.command :
                del self._requests_container[_n]

        self._requests_container.append(request, )
        return self

    def request (self, watch=False, timeout=constant.DEFAULT_TIMEOUT, ) :
        if not self._requests_container :
            raise _exceptions.RpcError('no requests registered.', )

        _requests = self._requests_container[:]
        self._requests_container = list()

        _missing_handshake = _requests[0].command != 'handshake'

        _stream_request = None

        _requests_container =  _requests[:]
        for i in _requests_container :
            # check whether the connection is still available or not.
            self._conn.connection

            if not self._conn.just_connected and i.command == 'handshake' :
                _requests.remove(i, )
                continue

            if self._conn.just_connected and _missing_handshake :
                self._request_handshake()

            if watch and i.is_stream :
                _stream_request = i

            self._request(i, )

        self._unpacker = msgpack.Unpacker(use_list=True, )

        _responses = self._handle_response(
                _requests,
                _stream_request,
                timeout=timeout,
            )

        self._initialize()
        return _responses

    def watch (self, timeout=None, ) :
        return self.request(watch=True, timeout=timeout, )

    def _handle_response (self, requests, stream_request=None, timeout=None, ) :
        if stream_request :
            self._got_first_stream_response = False
            timeout = None

        _requests = requests[:]
        _responses = list()
        while True :
            if not stream_request and not _requests :
                return _responses

            try :
                _response = self._get_response(
                            is_stream=bool(stream_request, )
                                if stream_request and self._got_first_stream_response else False,
                            timeout=timeout,
                        )
            except _exceptions.ConnectionLost :
                log.debug('connection lost.', )
                self._initialize(requests, reset_seq=True, )
                return self.request(watch=bool(stream_request), )
            except _exceptions.Disconnected :
                log.debug('disconnected', )
                return _responses

            _response.callback()
            if not stream_request :
                _responses.append(_response, )

            if stream_request :
                self._got_first_stream_response = True

            if _response.request.seq in self._command_handlers :
                try :
                    _requests.remove(_response.request, )
                except ValueError :
                    pass

        self._command_handlers = dict()
        if stream_request :
            self._got_first_stream_response = False

        return self.request_by_request(stream_request, ).request()

    def _request (self, request, ) :
        request.seq = self.seq
        self._command_handlers[self.seq] = request
        self.seq += 1

        log.debug('request %s' % (repr(request, ), ), )

        _method = getattr(self, '_request__%s' % request.command, self._request_default, )

        _method(request, )
        return

    def _request_default (self, request, ) :
        self._conn.write(request, )
        return

    def _get_response (self, is_stream=False, timeout=None, ) :
        class FoundBody (Exception, ) : pass

        _data = ''

        _header = None
        _request = None
        _body = list()
        _response_class = None
        while True :
            try:
                if not _data.startswith(constant.DATA_BEGIN_STRING, ) :
                    raise StopIteration

                _parsed = self._unpacker.next()
                if _header is not None :
                    if set(_parsed.keys()) == set(['Seq', 'Error', ], ) : # it's header
                        continue

                    _body.append(_parsed, )
                else :
                    if _parsed.get('Seq') not in self._command_handlers :
                        #raise RpcError('got invalid response: %s' % _header, )
                        continue

                    _header = _parsed
                    _request = self._command_handlers.get(_header.get('Seq'), )

                    _commands = list()
                    if is_stream :
                        _commands.append('%s_result' % (_request.command, ), )
                        _commands.append(_request.command, )
                    else :
                        _commands.append(_request.command, )

                    for i in _commands :
                        _response_class = RESPONSE_HANDLER.get(i, )
                        if _response_class is not None :
                            break

                    if not _response_class.has_body :
                        raise FoundBody
            except StopIteration :
                if _header and _body :
                    break

                _data = self._conn.read(timeout=timeout, )
                #log.debug('< got data: %s' % ((_data, ), ), )
                self._unpacker.feed(_data)
            except FoundBody :
                if _response_class is None :
                    raise _exceptions.RpcError('got invalid response', )

                break

        return _response_class(_request, _header, _body, )



