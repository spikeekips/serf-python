import socket

from . import _exceptions


class BaseResponse (object, ) :
    has_body = True

    def __init__ (self, request, header, body, ) :
        self.request = request
        self.header = header
        self._body = body

    def __repr__ (self, ) :
        return '<%s: %s, %s>' % (
                self.__class__.__name__,
                repr(self.request, ),
                self.header,
            )

    def _parse_body (self, ) :
        return self._body

    @property
    def body (self, ) :
        return self._parse_body()

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

    def __init__ (self, *a, **kw) :
        super(ResponseWithoutBody, self, ).__init__(*a, **kw)
        self._body = None if len(self._body) < 1 else self._body


class ResponseWithBody (BaseResponse, ) :
    has_body = True


class ResponseJoin (ResponseWithBody, ) :
    def __init__ (self, *a, **kw) :
        super(ResponseJoin, self, ).__init__(*a, **kw)
        self._body = None if len(self._body) < 1 else self._body[0]

    @property
    def is_success (self, ) :
        if not super(ResponseJoin, self).is_success or type(self._body) not in (dict, ) :
            return False

        return self._body.get('Num', 0, ) > 0


class ResponseMembers (ResponseWithBody, ) :
    def __init__ (self, *a, **kw) :
        super(ResponseMembers, self).__init__(*a, **kw)

        try :
            self._body = self._body[0]
        except IndexError :
            raise _exceptions.RpcError('invalid response body for members', )

        self._body_parsed = None

    def _parse_body (self, ) :
        # FIXME: in the current `serf` has bugs, https://github.com/hashicorp/serf/issues/158 .
        if self._body_parsed is None :
            self._body_parsed = dict(Members=list(), )
            for i in self._body.get('Members', ) :
                try :
                    i['Addr'] = self._parse_addr_field(i.get('Addr', ), )
                except (socket.error, ) :
                    i['Addr'] = None

                self._body_parsed['Members'].append(i, )

        return self._body_parsed

    def _parse_addr_field (self, a, ) :
        if type(a) not in (list, tuple, ) :
            return map(int, socket.inet_ntoa(a, ).split('.', ), )

        if type(a) in (str, unicode, ) :
            return map(int, a.split('.', ), )

        return a


