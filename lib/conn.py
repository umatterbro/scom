import socket
import proto
import logger

class connection:
    def __init__(self, sock: socket.socket, key_id: str, host: str = None, port: int = None, key_pwd: str = None):
        if(not isinstance(sock, socket.socket)): raise ValueError(f'sock must be of type socket, not {type(sock).__name__}')
        if(key_pwd is not None):
            if(not isinstance(key_pwd, str)): raise ValueError(f'key_pwd must be of type str, not {type(key_pwd).__name__}')

        self._socket = sock
        self.host = host
        self.port = port
        self.key_id = key_id
        self.key_pwd = key_pwd

    def send_packet(self, packet: proto.packet):
        if(not isinstance(packet, proto.packet)): raise ValueError(f'packet must be of type packet, not {type(packet).__name__}')
        logger.positive(f'sending packet')
        self._socket.sendall(packet.compile().data())

    def receive(self, bufsize: int = 65535):
        if(not isinstance(bufsize, int)): raise ValueError(f'bufsize must be of type int, not {type(bufsize).__name__}')
        data = self._socket.recv(bufsize)
        return data

def open(port: int, key_id: str, host: str = 'localhost', key_pwd: str = None):
    if(not isinstance(port, int)): raise ValueError(f'port must be of type int, not {type(port).__name__}')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    return connection(sock, key_id)
