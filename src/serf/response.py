import socket
import logging

from . import _exceptions


log = logging.getLogger('serf-rpc-client', )


class BaseResponse (object, ) :
    has_body = True
    has_more_responses = False

    def __init__ (self, request, header, body, ) :
        self.request = request
        self.header = header
        self.body = body

    def __repr__ (self, ) :
        return '<%s: %s, %s>' % (
                self.__class__.__name__,
                repr(self.request, ),
                self.header,
            )

    def _parse_body (self, body, ) :
        return body

    def _get_body (self, ) :
        return self._body

    def _set_body (self, body, ) :
        self._body = self._parse_body(body, )
        return

    body = property(_get_body, _set_body, )

    @property
    def seq (self, ) :
        return self.header.get('Seq', )

    @property
    def error (self, ) :
        return self.header.get('Error', )

    @property
    def is_success (self, ) :
        assert type(self.error) in (str, )

        return not self.error.strip()

    def callback (self, ) :
        if not self.request.callbacks :
            return

        for i in self.request.callbacks :
            i(self, )

        return self


class ResponseWithoutBody (BaseResponse, ) :
    has_body = False

    def _parse_body (self, body, ) :
        return None


class ResponseWithBody (BaseResponse, ) :
    has_body = True


class ResponseJoin (ResponseWithBody, ) :
    def _parse_body (self, body, ) :
        if not body or type(body) not in (dict, ) :
            return None

        return body

    @property
    def is_success (self, ) :
        if self.error :
            return False

        if type(self.body) not in (dict, ) :
            return False

        return self.body.get('Num', 0, ) > 0


class ResponseMembers (ResponseWithBody, ) :
    def _parse_body (self, body, ) :
        if not body :
            return

        # FIXME: in the current `serf` has bugs, https://github.com/hashicorp/serf/issues/158 .
        _parsed = dict(Members=list(), )
        for i in body.get('Members', ) :
            try :
                i['Addr'] = self._parse_addr_field(i.get('Addr', ), )
            except (socket.error, ) :
                i['Addr'] = None
        
            _parsed['Members'].append(i, )
        
        return _parsed

    def _parse_addr_field (self, a, ) :
        if type(a) not in (list, tuple, ) :
            return map(int, socket.inet_ntoa(a, ).split('.', ), )

        if type(a) in (str, unicode, ) :
            return map(int, a.split('.', ), )

        return a


class ResponseStream (ResponseWithBody, ) :
    has_more_responses = True

    def callback (self, ) :
        super(ResponseStream, self).callback()

        return None


class ResponseMonitor (ResponseWithBody, ) :
    has_more_responses = True

    def callback (self, ) :
        super(ResponseMonitor, self).callback()

        return None


class ResponseQuery (ResponseWithBody, ) :
    has_more_responses = True

    def callback (self, ) :

        if self.body.get('Type') in ('done', ) :
            self.has_more_responses = False

        return super(ResponseQuery, self).callback()

    def _parse_body (self, body, ) :
        if body and body.get('Type') in ('ack', ) and not body.get('From', ) :
            raise _exceptions.InvalidResponse('query `ack` response must have `From`.')

        if body and body.get('Type') in ('response', ) and not body.get('From', ) :
            raise _exceptions.InvalidResponse('query `response` response must have `From`.')

        return body

