import string
import msgpack

from . import _exceptions
from . import constant


class FunctionCommandCall (object, ) :
    def __init__ (self, command, client, ) :
        self._command = command
        self._client = client

    def __call__ (self, *a, **kw) :
        _request = self._client._get_request_class(
                self._command,
            )(*a, **kw).check(self._client, )

        self._client.request_by_request(_request, )

        return self._client


class BaseRequest (object ) :
    command = None
    command_translated = None
    need_watchful = False
    force_watchful = False

    must_be_argument = tuple()
    optional_argument = tuple()

    def __init__ (self, **body) :
        if self.command :
            self.command_translated = self.command.replace('_', '-', )

        self.seq = None
        self.body = body
        self.callbacks = list()

        self.is_checked = False

    def _get_is_checked (self, ) :
        return self._is_checked

    def _set_is_checked (self, b, ) :
        self._is_checked = b

    is_checked = property(_get_is_checked, _set_is_checked, )

    def check (self, client, ) :
        self.do_check(client, )

        self.is_checked = True

        return self

    def do_check (self, client, ) :
        # check argument
        _all_argument = set(self.must_be_argument) | set(self.optional_argument, )
        if not _all_argument :
            if self.body :
                raise _exceptions.InvalidRequest('request body be empty', )

        else :
            if not hasattr(self.body, 'keys', ) or not callable(self.body.keys, ) :
                raise _exceptions.InvalidRequest('invalid request body', )

            # check whether unknown arguments exist
            if set(self.body.keys()) - set(_all_argument) :
                raise _exceptions.InvalidRequest('unknown argument found in request', )

            # check must be arguments exist
            if set(self.must_be_argument, ) - set(self.body.keys()) :
                raise _exceptions.InvalidRequest('some argument missing in request', )

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

    @classmethod
    def dumps (cls, command, seq, body, ) :
        return msgpack.packb(dict(
                Command=command,
                Seq=seq,
            ), ) + (msgpack.packb(body, ) if body else '')

    def __str__ (self, ) :
        if not self.is_checked :
            raise _exceptions.UncheckedRequest

        if self.seq is None :
            self.seq = 0

        return self.dumps(
                self.command_translated,
                self.seq,
                self.body,
            )

    def add_callback (self, *callbacks) :
        self.callbacks.extend(callbacks)

        return self


class RequestHandshake (BaseRequest, ) :
    """
    {"Version": 1}
    """

    must_be_argument = ('Version', )

    def do_check (self, client, ) :
        if 'Version' not in self.body :
            self.body['Version'] = client.ipc_version

        super(RequestHandshake, self).do_check(client, )

        return


class RequestEvent (BaseRequest, ) :
    """
        {"Name": "foo", "Payload": "test payload", "Coalesce": true}
    """
    must_be_argument = (
            'Name',
            'Payload',
        )
    optional_argument = (
            'Coalesce',
        )

    def do_check (self, client, ) :
        super(RequestEvent, self).do_check(client, )

        if type(self.body.get('Name', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Name` must be str.', )

        if type(self.body.get('Payload', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Payload` must be str.', )

        if 'Coalesce' in self.body and type(self.body.get('Coalesce', ), ) not in (bool, ) :
            raise _exceptions.InvalidRequest('invalid request, `Coalesce` must be bool.', )

        # check payload
        self._is_checked = True
        if len(str(self.dumps('event', client.seq, self.body, )),
                        ) > constant.PAYLOAD_SIZE_LIMIT :
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
    need_watchful = True
    must_be_argument = (
            'Type',
        )

    def do_check (self, client, ) :
        super(RequestStream, self).do_check(client, )

        if type(self.body.get('Type', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        _types = filter(string.strip, self.body.get('Type').split(','), )
        if len(_types) < 1 :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be filled.', )

        return


class RequestLeave (BaseRequest, ) :
    def do_check (self, client, ) :
        super(RequestLeave, self).do_check(client, )

        return


class RequestForceLeave (BaseRequest, ) :
    """
        {"Node": "failed-node-name"}
    """
    must_be_argument = (
            'Node',
        )

    def do_check (self, client, ) :
        super(RequestForceLeave, self).do_check(client, )

        if type(self.body.get('Node', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        return


class RequestMonitor (BaseRequest, ) :
    """
        {"LogLevel": "DEBUG"}
    """
    need_watchful = True
    must_be_argument = (
            'LogLevel',
        )

    def do_check (self, client, ) :
        super(RequestMonitor, self).do_check(client, )

        if type(self.body.get('LogLevel', ), ) not in (str, unicode, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be str.', )

        return


class RequestStop (BaseRequest, ) :
    """
        {"Stop": 50}
    """
    must_be_argument = (
            'Stop',
        )

    def do_check (self, client, ) :
        super(RequestStop, self).do_check(client, )

        if type(self.body.get('Stop', ), ) not in (int, long, ) :
            raise _exceptions.InvalidRequest('invalid request, `Type` must be int.', )

        return


class RequestJoin (BaseRequest, ) :
    """
        {"Existing": ["192.168.0.1:6000", "192.168.0.2:6000"], "Replay": false}
    """
    must_be_argument = (
            'Existing',
            'Replay',
        )

    def do_check (self, client, ) :
        super(RequestJoin, self).do_check(client, )

        if type(self.body.get('Existing', ), ) not in (list, tuple, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Existing` must be list or tuple.', )

        if self.body.get('Replay', ) and type(self.body.get('Replay', ), ) not in (bool, ) :
            raise _exceptions.InvalidRequest('invalid request, `Replay` must be bool.', )

        return


class RequestQuery (BaseRequest, ) :
    """
    {
        "FilterNodes": ["foo", "bar"],
        "FilterTags": {"role": ".*web.*"},
        "RequestAck": true,
        "Timeout": 0,
        "Name": "load",
        "Payload": "15m",
    }
    """
    force_watchful = True
    must_be_argument = (
            'Name',
        )
    optional_argument = (
            'FilterNodes',
            'FilterTags',
            'RequestAck',
            'Timeout',
            'Payload',
        )

    def do_check (self, client, ) :
        super(RequestQuery, self).do_check(client, )

        if type(self.body.get('Name', ), ) not in (str, unicode, ) :
            self.body['Name'] = str(self.body.get('Name'), )

        if self.body.get('FilterNodes', ) and type(self.body.get('FilterNodes', ),
                        ) not in (list, tuple, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `FilterNodes` must be list or tuple.', )

        if self.body.get('FilterTags', ) and type(self.body.get('FilterTags', ),
                        ) not in (dict, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `FilterNodes` must be dict.', )

        if 'RequestAck' in self.body and type(self.body.get('RequestAck', ),
                        ) not in (bool, ) :
            #raise _exceptions.InvalidRequest('invalid request, `RequestAck` must be bool.', )
            self.body['RequestAck'] = bool(self.body.get('RequestAck'), )

        if 'Timeout' in self.body and type(self.body.get('Timeout', ),
                        ) not in (float, int, long, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Timeout` must be float, int or long.', )

        # check payload
        self._is_checked = True

        if len(str(self.dumps('respond', client.seq, self.body, )), 
                    ) > constant.RESPOND_PAYLOAD_SIZE_LIMIT :
            raise _exceptions.InvalidRequest(
                    'invalid request, message size must be smaller than %s.' % (
                            constant.RESPOND_PAYLOAD_SIZE_LIMIT,
                        ), )
        self._is_checked = False

        return

class RequestRespond (BaseRequest, ) :
    """
    {"ID": 1023, "Payload": "my response"}
    """
    must_be_argument = (
            'ID',
            'Payload',
        )

    def do_check (self, client, ) :
        super(RequestRespond, self).do_check(client, )

        if type(self.body.get('ID', ), ) not in (int, long, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Existing` must be int or long.', )

        # check payload
        self._is_checked = True

        if len(str(self.dumps('respond', client.seq, self.body, )),
                        ) > constant.RESPOND_PAYLOAD_SIZE_LIMIT :
            raise _exceptions.InvalidRequest(
                    'invalid request, message size must be smaller than %s.' % (
                            constant.RESPOND_PAYLOAD_SIZE_LIMIT,
                        ), )
        self._is_checked = False

        return


class RequestMembers (BaseRequest, ) :
    """
    {"Tags": {"key": "val"}, "Status": "alive", "Name": "node1"}
    """
    optional_argument = (
            'Tags',
            'Status',
            'Name',
        )

    def do_check (self, client, ) :
        super(RequestMembers, self).do_check(client, )

        if set(self.optional_argument) & set(self.body.keys()) :
            self.command_translated = 'members-filtered'

        if self.body.get('Tags') and type(self.body.get('Tags')) not in (dict, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Tags` must be dict.', )

        return


class RequestTags (BaseRequest, ) :
    """
    {"Tags": {"tag1": "val1"}, "DeleteTags": ["tag2"]}
    """
    optional_argument = (
            'Tags',
            'DeleteTags',
        )

    def do_check (self, client, ) :
        super(RequestTags, self).do_check(client, )

        if 'Tags' not in self.body and 'DeleteTags' not in self.body :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Tags` or `DeleteTags` must be given.', )

        if self.body.get('Tags') and type(self.body.get('Tags')) not in (dict, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `Tags` must be dict.', )

        if self.body.get('DeleteTags') and type(self.body.get('DeleteTags'),
                        ) not in (list, tuple, ) :
            raise _exceptions.InvalidRequest(
                    'invalid request, `DeleteTags` must be list or tuple.', )

        return



