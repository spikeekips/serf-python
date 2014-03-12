import string

from .request import (
        BaseRequest,
        RequestEvent,
        RequestHandshake,
        RequestJoin,
        RequestLeave,
        RequestForceLeave,
        RequestMonitor,
        RequestStop,
        RequestStream,
    )
from .response import (
        ResponseJoin,
        ResponseMembers,
        ResponseWithBody,
        ResponseWithoutBody,
    )

_REQUEST_HANDLER = {
        'handshake': RequestHandshake,
        'event': RequestEvent,
        'force_leave': RequestForceLeave,
        'join': RequestJoin,
        'members': BaseRequest,
        'stream': RequestStream,
        'monitor': RequestMonitor,
        'stop': RequestStop,
        'leave': RequestLeave,
    }


_RESPONSE_HANDLER = {
        'handshake': ResponseWithoutBody,
        'event': ResponseWithoutBody,
        'force_leave': ResponseWithoutBody,
        'join': ResponseJoin,
        'members': ResponseMembers,
        'stream': ResponseWithoutBody,
        'stream_result': ResponseWithBody,
        'monitor': ResponseWithBody,
        'monitor_result': ResponseWithBody,
        'stop': ResponseWithoutBody,
        'leave': ResponseWithoutBody,
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



