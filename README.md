# serf client for python [![Build Status](https://travis-ci.org/spikeekips/serf-python.png?branch=master)](https://travis-ci.org/spikeekips/serf-python)


`serf-python` is the python client for `serf` (python3.x not yet).

`serf` is the simple and lightweight clustering software, you can easily create the cluster for your own application. For more details on `serf`, please visit, http://www.serfdom.io/ . `serf` is still in early stage of development, but has already the necessary features for production environment.


## Installation

```sh
$ pip install serf-python
```

or, from source.

```sh
$ git clone git@github.com:spikeekips/serf-python.git
$ cd serf-python

$ git checkout v0.1

$ python setup.py install
```

## Usage

`serf` provides the commands to communicate with `serf` agent thru *RPC*, based on `msgpack`. Naturally `serf-python` use the *RPC* protocol. `serf-python` supports these `serf` commands,

* handshake
* auth
* event
* force-leave
* join
* members
* stream
* monitor
* stop
* leave
* query
* respond

~~`serf` provides some more commands like `auth`, these will be supported as soon as possible. :)~~ `serf-python` is supporting all the available commands of `serf`, you can find the all the supported commands in http://www.serfdom.io/docs/agent/rpc.html .

Each command has it's own arguments, which are described in *RPC* command page http://www.serfdom.io/docs/agent/rpc.html . `serf-python` exactly follows naming and rules of these arguments, including case-sensitive, so you can use the same arguments of the *RPC* commands in `serf`.


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

attribute         | type    | description
---               | ---     | ---
**header**        | *dict*  | response header, ``` {'Error': '', 'Seq': 1} ```
**body**          | -       | body message
**seq**           | *int*   | requested `Seq`
**error**         | *str*   | error message
**is_success**    | *bool*  | command is successful or not(contextual).

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

For streaming command like `stream` or `monitor`, you can use `watch`. `watch` will wait and stream the response from `serf` agent until you manually stop it using `stop` command, and your `callback` will be executed in every response.

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

To handle the responses for the stream commands, you can set the callbacks by `add_callback()` method, which will handle the each response by command.

If you use `request` for the stream commands, the responses will wait until the timeout you set, the default timeout is 2 seconds, whcih is defined in `serf.constant.DEFAULT_TIMEOUT`.


### Commands

The description and arguments for each command, please refer this page, http://www.serfdom.io/docs/agent/rpc.html .


#### handshake

In `serf` thru *RPC*, you must request the `handshake` command ahead of any other commands, so `serf-python` will automatically request `handshake` even you omit it.

```python
>>> _client = serf.Client()
>>> _responses = _client.handshake().request()
[
    <ResponseHandshake: <RequestHandshake: handshake, 0, {'Version': 1}>, {'Seq': 0, 'Error': ''}>
]
>>> _responses[0].is_sucess
True
```

You can bypass the `handshake` command for convenience, this is safe and easy way.

```python
>>> _client = serf.Client()
>>> _responses = _client.members().request()
```


#### auth

```python
>>> _responses = _client.auth(AuthKey='valid-authkey', ).request()
>>> _responses
[
    <ResponseHandshake: <RequestHandshake: handshake, 0, {'Version': 1}>, {'Seq': 0, 'Error': ''}>,
    <ResponseAuth: <RequestAuth: auth, 1, {'AuthKey': 'valid-authkey'}>, {'Seq': 1, 'Error': ''}>
]
>>> _responses[1].seq
1
>>> _responses[1].error
''
>>> _responses[1].header
{'Error': '', 'Seq': 1}
>>> _responses[1].body
None
```

If error occured, it will raise `serf.AuthenticationError`.

```python
>>> _responses = _client.auth(AuthKey='bad-authkey', ).request()
Traceback (most recent call last):
...
serf.AuthenticationError: failed to authed, ('127.0.0.1', 7374, {}).
```

You can set the `AuthKey` in hosts url, and then you can ommit this `auth` command like `handshake`.

```python
>>> _client = serf.Client('serf://127.0.0.1:7373?AuthKey=valid-authkey', )
>>> _responses = _client.members().request()
```

See below in this page about the hosts url.


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
> &nbsp;&nbsp;&nbsp;&nbsp;In `serf`, the payload size has limitation, you can send event message up to 1KB, see 'Custom Event Limitations' section in http://www.serfdom.io/intro/getting-started/user-events.html . Manually tune the payload size limit, see `serf.constant.PAYLOAD_SIZE_LIMIT`.


#### join

```python
>>> _responses = _client.join(
...        Existing=('127.0.0.1:7900', ),
...        Replay=False,
...    ).request()
>>> _responses
[
    <ResponseJoin: <RequestJoin: join, 1, {'Replay': False, 'Existing': ('127.0.0.1:7900',)}>, {'Seq': 1, 'Error': ''}>
]
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

You can get all the members without any *filtered* arguments.

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
              'Tags': {'role': 'dummy'}},
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

You also can filter the members with *filtered* arguments. With *filters*, it will use the `members-filtered` command instead of `members` command.

```python
>>> _responses = _client.members(Status='alive', Tags=dict(role='dummy', ), ).request()
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
              'Tags': {'role': 'dummy'}}]}
```

The filtering conditions will be joined as ```AND (&)``` operator, that is, `serf` will return the members, which are satisfied to all the filter condition.

You can find the available `Status` at https://github.com/hashicorp/serf/blob/master/serf/serf.go#L101 .

#### tags

```python
>>> _responses = _client.tags(
...        Tags=dict(role='dummy', ),
...        DeleteTags=('critical', ),
...    ).request()
>>> _responses[0]
<ResponseTags: <RequestTags: tags, 1, {'DeleteTags': ('critical',), 'Tags': {'role': 'dummy'}}>, {'Seq': 1, 'Error': ''}>
>>> _responses[0].seq
1
>>> _responses[0].is_success
''
>>> _responses[0].header
{'Error': '', 'Seq': 1}
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
...     pprint.pprint(response.body, )


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
...      print response

>>> _client.monitor(LogLevel='DEBUG', ).add_callback(_callback_monitor, ).request()
```

You can find the available `LogLevel` at https://github.com/hashicorp/serf/blob/a7d854a1b598975f687771e8975d32c8dfbc8319/command/agent/log_levels.go#L12 .

With `request()`, you can just get the latest log messages. With `watch()` like `stream().watch()`, you can get the continuous log messages.


#### stop

```python
>>> def _callback_stream (response, ) :
...     # get `Seq` for `stop`
...     _seq = response.seq
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


#### query

```python
>>> def _callback_query (response, ) :
...     if not response.is_sucess :
...         raise ValueError(response.error, )
...
...     print response
...     return

>>> _response = _client.query(
...        Name='response-me',
...        Payload='this is payload of `response-me` query event',
...    ).add_callback(_callback_query, ).request()

>>> _response.is_sucess
True
>>> len(_response)
3
>>> for i in _response :
...     print i.body
{'From': 'node0', 'Payload': None, 'Type': 'ack'}
{'From': 'node0', 'Payload': '.......', 'Type': 'response'}
{'From': '', 'Payload': None, 'Type': 'done'}
```

In this example, we use `request()`, but `query` command will wait until the `done` response is received.


#### respond

```python
>>> def _callback_respond (response, ) :
...     if not response.is_sucess :
...         raise ValueError(response.error, )
...
...     return
...
>>> def _callback_stream (response, ) :
...     print '> got stream response.'
... 
...     if response.body :
...         if response.body.get('Event') in ('query', ) :
...             # send respond back.
...             _client.respond(
...                     ID=response.body.get('ID'),
...                     Payload='this is payload',
...                     Timeout=10,
...                 ).add_callback(_callback_respond, ).request()
... 
>>> _client.stream(Type='query', ).add_callback(_callback_stream, ).watch()
```

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


### Stop `watch`ing

Basically `watch` will keep receiving response until you manually disconnect or exception is occured. If you want to stop `watch`ing in specific condition, you can raise `_exception.StopReceiveData`.

```python
>>> def _callback_stream (response, ) :
...     print '> got stream response.'
... 
...     if response.body :
...         if response.body.get('Event') in ('query', ) :
...             _client.stop(Stop=response.seq, )
...             raise _exception.StopReceiveData
... 
>>> _client.stream(Type='*', ).add_callback(_callback_stream, ).watch()
```

This will stop watching when `query` event is received, but `stop` request will not send automatically.


### Use `with` Statement For One Time Request

```python
>>> with serf.Client('127.0.0.1:7373,127.0.0.1:7374', ) as _client :
...     _client.members().request
```

The outside of `with` block, the `_client` will be automatically be disconnect after getting response for `members`.


### Host URL

To connect to the serf agent, you need to set the host url in the `Client` like this,

```python
>>> serf.Client()
```

This will connect to the default *RPC* host, `127.0.0.1` and port, `7373`.

```python
>>> serf.Client('127.0.0.1:7373,127.0.0.1:7374', )
```

This will connect to the `127.0.0.1:7373` at first, if it is failed, try to the next one, `127.0.0.1:7374`.

```python
>>> serf.Client('serf://127.0.0.1:7373?AuthKey=valid-authkey', )
```

If your agent needs *RPC* `auth_token`, you can set the `AuthKey` in the host url. As you see, this is valid URI format.

```
serf://<host>:<port>?AuthKey=<auth key>
```


## Todo and Next...

* ~~support the missing command, `auth`, etc.~~
* support various environment, Django, flask, etc.


## Participate Developing

Please share where and how you are using the `serf-python`.


