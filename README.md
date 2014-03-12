# serf client for python [![Build Status](https://travis-ci.org/spikeekips/serf-python.png?branch=master)](https://travis-ci.org/spikeekips/serf-python)


`serf-python` is the client for `serf` for python(python3.x not yet).

`serf` is the simple and lightweight clustering software, you can easily create the cluster for your own application. For more details on `serf`, please visit, http://www.serfdom.io/ . `serf` is still in early stage of development, but has already the necessary features for production environment.


## Installation

```sh
$ pip install serf-python
```

or from source.

```sh
$ git clone git@github.com:spikeekips/serf-python.git
$ cd serf-python

$ git checkout v0.1 

$ python setup.py install
```

## Usage

`serf` provides the commands to communicate with `serf` agent thru *RPC*, based on `msgpack`. Naturally `serf-python` use the *RPC* protocol. `serf-python` supports these `serf` commands,

command         |
---             |
*handshake*     |
*event*         |
*force-leave*   |
*join*          |
*members*       |
*stream*        |
*monitor*       |
*stop*          |
*leave*         |

`serf` provides some more commands like `auth`, these will be supported as soon as possible. :) You can find the all the supported commands in http://www.serfdom.io/docs/agent/rpc.html .


### Basic Usage

To connect to your `serf` agent,

```python
>>> import serf
>>> _client = serf.Client('127.0.0.1:7373,127.0.0.1:7374', auto_reconnect=False, )
```

The above example, ```127.0.0.1:7373,127.0.0.1:7374``` is the two agent addresses,
 
* ```127.0.0.1:7373```: host: localhost, port: 7373
* ```127.0.0.1:7374```: host: localhost, port: 7374

You can address the multiple agent addresses as long as you want, just seperates by comma(,), so it will automatically try to reconnect to the next another agent address when accidentally lose connection. This feature will be enabled by `auto_reconnect=True` option, default is `False`.

At this stage, `Client` does not connect to the agent, if you want connect manually,

```python
>>> _client = serf.Client('127.0.0.1:7373,127.0.0.1:7374', auto_reconnect=False, )
>>> _client.connect()
```


### disconnect

```python
>>> _client.disconnect()
```


### How To Request Command

```python
>>> _client.<command name>()
>>> _client.<another command name>()
>>> _responses = _client.request()
[
    <Response: <Request: ...>, {'Seq': 0, 'Error': ''}>,
    <Response: <Request: ...>, {'Seq': 1, 'Error': ''}>
]
```

Before call `request()` or `watch()`, any command will not be delivered to the agent.


#### Response

The response, `_responses` is `list` type, which is ordered by `Seq` and the `Response` has the following attributes,

attribute       | type  | description
---             | ---   | ---
*header*        | dict  | response header, ``` {'Error': '', 'Seq': 1} ```
*body*          | -     | body message
*seq*           | int   | requested `Seq`
*error*         | str   | error message
*is_success*    | bool  | command is successful or not(contextual).

```python
>>> _responses[0].seq
0
>>> _responses[1].seq
1
>>> _responses[0].header
{'Error': '', 'Seq': 0}
>>> _responses[1].header
{'Error': '', 'Seq': 1}
>>> _responses[0].body
{...}
>>> _responses[1].body
{...}
```

#### timeout

```python
>>> _client.<command>.request(timeout=5, )
```



#### Using callback

You can manually assign the callback for specific command like this,

```python
>>> _callback_member_one (response, ) :
...     print response

>>> _callback_member_two (response, ) :
...     print response

>>> _callback_join (response, ) :
...     print response

>>> _client.members().add_callback(_callback_member_one, _callback_member_two, )
>>> _client.join(Existing=('127.0.0.1:7902', ), Replay=True,).add_callback(_callback_join,)
>>> _client.request()
```

The callbacks will be executed by order.


#### Streaming Response

For streaming command like `stream` or `monitor` you can use `watch`, you can
find the available `LogLevel` at https://github.com/hashicorp/serf/blob/a7d854a1b598975f687771e8975d32c8dfbc8319/command/agent/log_levels.go#L12 .

```python
>>> def _callback (response, ) :
...     if not response.is_sucess :
...         raise ValueError(response.error, )
... 
...     print response.body

>>> _client.stream().add_callback(_callback, ).watch()
>>> # or
>>> _client.stream().add_callback(_callback, ).request(watch=True, )
```

In the stream commands, to handle the responses, you can set the callbacks by `add_callback()` method

`watch` will wait and stream the response from `serf` agent until you manually stop it using `stop` command, and your `callback` will be executed in every response.


### Commands

The description and arguments for each command, please refer this page, http://www.serfdom.io/docs/agent/rpc.html .


#### handshake

In `serf` thru *RPC*, you must request the `handshake` command ahead of any other commands, but `serf-python` will automatically request `handshake` even you omit it.

```python
>>> _responses = _client.handshake().request()
[
    <ResponseHandshake: <RequestHandshake: handshake, 0, {'Version': 1}>, {'Seq': 0, 'Error': ''}>
]
>>> _responses[0].is_sucess
True
```

You can bypass the `handshake` command for convenience,

```python
>>> _responses = _client.members().request()
```

#### event

```python
>>> _responses = _client.event(
...         Name='event-name',
...         Payload='this is payload to be broadcasted to all members',
...         Coalesce=True,
...     ).request()
>>> _responses[0]
<ResponseEvent: <RequestEvent: event, 1, {'Coalesce': True, 'Name': 'test-event', 'Payload': 'test message'}>, {'Seq': 1, 'Error': ''}>
>>> _responses[0].seq
1
>>> _responses[0].error
''
>>> _responses[0].header
{'Error': '', 'Seq': 1}
>>> _responses[0].body
None
```

> NOTE:
> 
> &nbsp;&nbsp;&nbsp;&nbsp;In `serf`, the payload size has limitation, you can send event message up to 1KB, see 'Custom Event Limitations' section in http://www.serfdom.io/intro/getting-started/user-events.html .
> To manually tune the payload size limit, see `serf.constant.PAYLOAD_SIZE_LIMIT`.


#### join

```python
>>> _responses = _client.join(
...        Existing=('127.0.0.1:7900', ),
...        Replay=False,
...    ).request()
>>> _responses[0]
[<ResponseJoin: <RequestJoin: join, 1, {'Replay': False, 'Existing': ('127.0.0.1:7900',)}>, {'Seq': 1, 'Error': ''}>]
>>> _responses[0].seq
1
>>> _responses[0].error
''
>>> _responses[0].header
{'Error': '', 'Seq': 1}
>>> _responses[0].body
{'Num': 1}
```

If the `Num` is less than 1 in the response body, `is_success` will be `False`.


#### members

```python
>>> _responses = _client.members().request()
>>> _responses[0]
<ResponseMembers: <RequestMembers: members, 2, >, {'Seq': 2, 'Error': ''}>
>>> _responses[0].seq
1
>>> _responses[0].error
''
>>> _responses[0].header
{'Error': '', 'Seq': 1}
>>> _responses[0].body
{'Members': [{'Addr': [127, 0, 0, 1],
              'DelegateCur': 4,
              'DelegateMax': 4,
              'DelegateMin': 2,
              'Name': 'node3',
              'Port': 7900,
              'ProtocolCur': 2,
              'ProtocolMax': 2,
              'ProtocolMin': 1,
              'Status': 'alive',
              'Tags': {}},
             ...
             {'Addr': [127, 0, 0, 1],
              'DelegateCur': 4,
              'DelegateMax': 4,
              'DelegateMin': 2,
              'Name': 'node1',
              'Port': 7901,
              'ProtocolCur': 2,
              'ProtocolMax': 2,
              'ProtocolMin': 1,
              'Status': 'alive',
              'Tags': {}}]}
```


#### stream

```python
>>> def _callback_stream (response, ) :
...     print '> got stream response.'
...     
...     print 'response:', response
...     print 'seq:', response.seq
...     print 'error:', (response.error, )
...     print 'header:',
...     pprint.pprint(response.header, )
...     
...     print 'events:'
...     if response.body :
...         for _event in response.body :
...             pprint.pprint(_event, )


...     return

>>> _client.stream(Type='*', ).watch()
>>> # or
>>> _client.stream(Type='*', ).request()
```

When the new event is occured, you will get these kind of messages,

```
response: <ResponseStreamResult: <RequestStream: stream, 3, {'Type': '*'}>, {'Seq': 3, 'Error': ''}>
seq: 3
error: ('',)
header:{'Error': '', 'Seq': 3}
events:
{'Coalesce': True,
 'Event': 'user',
 'LTime': 13,
 'Name': 'test-event',
 'Payload': 'test message'}
```

You can filter the stream event using `Type`, for details, see stream section in http://www.serfdom.io/docs/agent/rpc.html .

#### monitor

```python
>>> def _callback_monitor (response, ) :
..      print response

>>> _client.monitor(LogLevel='DEBUG', ).add_callback(_callback_monitor, ).request()
```

With `request()`, you can just get the latest log messages. With `watch()` like `stream().watch()`, you can get the continuous log messages.


#### stop

```python
>>> def _callback_stream (response, ) :
...     # get `Seq` for `stop`
...     _seq = resonse.seq
...     _client.stop(Stop=_seq, )
...     return

>>> _client.stream(Type='*', ).add_callback(_callback_stream, ).watch()
```


#### leave

```python
>>> _client.connect().force_leave().request()
```


#### force-leave

```python
>>> _client.connect().force_leave(Node='node1', ).request()
```

or as a `Node` value, you can use the node name, which is the `Name` value in the response of `members` command.


## Tips and Tricks

### Chaining Commands

You can request multiple command at once like this,

```python
>>> _responses = _client.members().join(Existing=('127.0.0.1:7902', ),Replay=True, ).request()
```

This chains two commands, `members` and `join`.

### Disconnect After Getting Response

If you disconnect after getting the responses,

```python
>>> _responses = _client.members(
...     ).join(
...         Existing=('127.0.0.1:7902', ),
...         Replay=True,
...     ).disconnect(wait=True, ).request()
>>> _responses
```

Without `wait=True`, it will just close the connection before sending requests.

## Todo and Next...

* support the missing commands, `tags`, `auth`, etc.
* support various environment, Django, flask, etc.
* support context manager.


