import string

from .request import (
        RequestEvent,
        RequestHandshake,
        RequestJoin,
        RequestLeave,
        RequestForceLeave,
        RequestMonitor,
        RequestStop,
        RequestMembers,
        RequestTags,
        RequestStream,
        RequestQuery,
        RequestRespond,
    )

from .response import (
        ResponseJoin,
        ResponseMembers,
        ResponseWithoutBody,
        ResponseStream,
        ResponseMonitor,
        ResponseQuery,
    )

_REQUEST_HANDLER = {
        'handshake': RequestHandshake,
        'event': RequestEvent,
        'force_leave': RequestForceLeave,
        'join': RequestJoin,
        'members': RequestMembers,
        'tags': RequestTags,
        'stream': RequestStream,
        'monitor': RequestMonitor,
        'stop': RequestStop,
        'leave': RequestLeave,
        'query': RequestQuery,
        'respond': RequestRespond,
    }


_RESPONSE_HANDLER = {
        'handshake': ResponseWithoutBody,
        'event': ResponseWithoutBody,
        'force_leave': ResponseWithoutBody,
        'join': ResponseJoin,
        'members': ResponseMembers,
        'tags': ResponseWithoutBody,
        'stream': ResponseStream,
        'monitor': ResponseMonitor,
        'stop': ResponseWithoutBody,
        'leave': ResponseWithoutBody,
        'query': ResponseQuery,
        'respond': ResponseWithoutBody,
    }


REQUEST_HANDLER = dict()
for k, v in _REQUEST_HANDLER.items() :
    REQUEST_HANDLER[k] = type(
            'Request%s' % ''.join(map(string.capitalize, k.split('_'), ), ),
            (v, ),
            dict(command=k, ),
        )

RESPONSE_HANDLER = dict()
for k, v in _RESPONSE_HANDLER.items() :
    RESPONSE_HANDLER[k] = type(
            'Response%s' % ''.join(map(string.capitalize, k.split('_'), ), ),
            (v, ),
            dict(),
        )



