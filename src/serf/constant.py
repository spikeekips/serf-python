DEFAULT_IPC_VERSION = 1
DEFAULT_READ_BUFFER_SIZE = 8192 * 100
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 7373
DEFAULT_TIMEOUT = 2
PAYLOAD_SIZE_LIMIT = 256
STREAM_COMMANDS = ('stream', 'monitor', )
DATA_BEGIN_STRING = '\x82\xa5'
WRITE_RETRY = 3
CONNECTION_RETRY = 3
CONNECTION_RETRY_INTERVAL = 2


COMMAND_LIST = (
        'handshake',
        'event',
        'force_leave',
        'join',
        'members',
        'stream',
        'monitor',
        'stop',
        'leave',
    )


