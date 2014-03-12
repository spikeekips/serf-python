import string
import msgpack

from . import _exceptions
from . import constant


class BaseRequest (object ) :
    command = None

    def __init__ (self, **body) :
        self.seq = None
        self.body = body
        self.callbacks = list()

        self._is_checked = False

    def check (self, client, ) :
        self.do_check(client, )

        self._is_checked = True

        return self

    def do_check (self, client, ) :
        return

    def __getstate__ (self, ) :
        return dict(
                command=self.command,
                seq=self.seq,
                body=self.body,
                callbacks=self.callbacks,
            )

    def __repr__ (self, ) :
        return '<%s: %s, %s, %s>' % (
                self.__class__.__name__,
                self.command,
                self.seq,
                str(self.body) if self.body else '',
            )

    def __str__ (self, ) :
        if not self._is_checked :
            raise _exceptions.UncheckedRequest

        if self.seq is None :
            self.seq = 0

        return msgpack.packb(dict(
                Command=self.command.replace('_', '-', ),
                Seq=self.seq,
            ), ) + (msgpack.packb(self.body, ) if self.body else '')

    @property
    def is_stream (self, ) :
        return self.command in constant.STREAM_COMMANDS

    def add_callback (self, *callbacks) :
        self.callbacks.extend(callbacks)

        return self


class RequestHandshake (BaseRequest, ) :
    """
    {"Version": 1}
    """
    def do_check (self, client, ) :
        if 'Version' not in self.body :
            self.body['Version'] = client.ipc_version

        return


class RequestEvent (BaseRequest, ) :
    """
        {"Name": "foo", "Payload": "test payload", "Coalesce": true}
    """
    _available_body_parameters = (
            'Name',
            'Payload',
            'Coalesce',
        )

    def do_check (self, client, ) :
        if set(self.body.keys()) - set(self._available_body_parameters) :
            raise _exceptions.InvalidRequest('invalid request', )

        try :
            self.body['Name']
            self.body['Payload']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Name', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Name` must be str.', )

        if type(self.body.get('Payload', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Payload` must be str.', )

        if type(self.body.get('Coalesce', ), ) not in (bool, ) :
            raise _exceptions.InvalidRequest('invalid request, `Coalesce` must be bool.', )

        # check payload
        self._is_checked = True
        if len(str(self)) > constant.PAYLOAD_SIZE_LIMIT :
            raise _exceptions.InvalidRequest(
                    'invalid request, message size must be smaller than %s.' % (
                            constant.PAYLOAD_SIZE_LIMIT,
                        ), )
        self._is_checked = False

        return


class RequestStream (BaseRequest, ) :
    """
        {"Type": "member-join,user:deploy"}`
    """
    _available_body_parameters = (
            'Type',
        )

    def do_check (self, client, ) :
        if set(self.body.keys()) - set(self._available_body_parameters) :
            raise _exceptions.InvalidRequest('invalid request', )

        try :
            self.body['Type']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Type', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        _types = filter(string.strip, self.body.get('Type').split(','), )
        if len(_types) < 1 :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be filled.', )

        return


class RequestLeave (BaseRequest, ) :
    _available_body_parameters = ()

    def do_check (self, client, ) :
        if self.body.keys() :
            raise _exceptions.InvalidRequest('invalid request', )

        return


class RequestForceLeave (BaseRequest, ) :
    """
        {"Node": "failed-node-name"}
    """
    _available_body_parameters = (
            'Node',
        )

    def do_check (self, client, ) :
        if set(self.body.keys()) - set(self._available_body_parameters) :
            raise _exceptions.InvalidRequest('invalid request', )

        try :
            self.body['Node']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Node', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        return


class RequestMonitor (BaseRequest, ) :
    """
        {"LogLevel": "DEBUG"}
    """
    _available_body_parameters = (
            'LogLevel',
        )

    def do_check (self, client, ) :
        if set(self.body.keys()) - set(self._available_body_parameters) :
            raise _exceptions.InvalidRequest('invalid request', )

        try :
            self.body['LogLevel']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('LogLevel', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        return


class RequestStop (BaseRequest, ) :
    """
        {"Stop": 50}
    """
    _available_body_parameters = (
            'Stop',
        )

    def do_check (self, client, ) :
        if set(self.body.keys()) - set(self._available_body_parameters) :
            raise _exceptions.InvalidRequest('invalid request', )

        try :
            self.body['Stop']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Stop', ), ) not in (int, long, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be int.', )

        return


class RequestJoin (BaseRequest, ) :
    """
        {"Existing": ["192.168.0.1:6000", "192.168.0.2:6000"], "Replay": false}
    """
    _available_body_parameters = (
            'Existing',
            'Replay',
        )

    def do_check (self, client, ) :
        if set(self.body.keys()) - set(self._available_body_parameters) :
            raise _exceptions.InvalidRequest('invalid request', )

        try :
            self.body['Existing']
        except KeyError :
            raise _exceptions.InvalidRequest('invalid request, some key is missing.', )

        if type(self.body.get('Existing', ), ) not in (list, tuple, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Existing` must be list or tuple.', )

        if self.body.get('Replay', ) and type(self.body.get('Replay', ), ) not in (bool, ) :
            raise _exceptions.InvalidRequest('invalid request, `Replay` must be bool.', )

        return


