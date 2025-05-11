import cfgmgr
import proto
import conn
import socket
import logger
import threading
import partitioner

class scom:
    class method_handler:
        class method:
            def __init__(self, flag: proto.packet.tds_s.flag_cont.flag, callback):
                if(not isinstance(flag, proto.packet.tds_s.flag_cont.flag)): raise ValueError(f'flag must be of type flag, not {type(flag).__name__}')
                if(not callable(callback)): raise ValueError(f'callback cannot be called')

                self.flag = flag
                self.callback = callback

            def call(self, *args, **kwargs):
                return self.callback(args, kwargs)

        def __init__(self):
            self._methods = []

        def method_name_exists(self, method_name: str):
            for method in self._methods:
                if(method.callback.__name__ == method_name): return True
            return False

        def method_flag_exists(self, method_flag: proto.packet.tds_s.flag_cont.flag):
            for method in self._methods:
                if(method.flag == method_flag): return True
            return False

        def reg_method(self, method: method):
            if(not isinstance(method, self.method)): raise ValueError(f'method must be of type method, not {type(method).__name__}')
            if(self.method_name_exists(method.callback.__name__)): raise ValueError(f'method name {method.callback.__name__} already registered')
            if(self.method_flag_exists(method.flag)): raise ValueError(f'method flag {method.flag.name} already registered')

            self._methods.append(method)
            logger.debug(f'registered {method.callback.__name__} to {method.flag.name}')

        def get_callback(self, flag: proto.packet.tds_s.flag_cont.flag):
            for method in self._methods:
                if(method.flag == flag): return method.callback
            return None

    class conn_handler:
        def __init__(self):
            self._connections = []

        def handle_conn(self, conn: conn.connection):
            if(not isinstance(conn, conn.connection)): raise ValueError(f'conn must be of type connection, not {type(conn).__name__}')
            
            logger.positive(f'now handling {conn.host}:{conn.port}')
            while True:
                try: data = conn.receive()
                except ConnectionResetError:
                    logger.negative(f'ending connection with {conn.host}:{conn.port}')
                    break
                except Exception as ex:
                    logger.negative(f'unhandled exception {type(ex).__name__} occured: {str(ex)}')
                    continue

                if(not data): break
                print(f'data: {data}')

                conn._socket.sendall(b'hi')

        def reg_conn(self, conn: conn.connection):
            self._connections.append(conn)

            thr = threading.Thread(target=self.handle_conn, args=(conn))

    def __init__(self, config_mgr: cfgmgr.config_manager):
        if(not isinstance(config_mgr, cfgmgr.config_manager)): raise ValueError(f'config manager must be of type cfgmgr.config_manager, not {type(config_mgr).__name__}')

        self.config_mgr = config_mgr
        self.conn_mgr = self.conn_handler()
        self.mtd_mgr = self.method_handler()
        self._method_map = {}

    def froute(self, flag):
        if(not isinstance(flag, proto.packet.tds_s.flag_cont.flag)): raise ValueError(f'flag must be of type flag, not {type(flag).__name__}')
        def inner(func):
            def wrapper(packet, data):
                return func(packet, data)

            self.mtd_mgr.reg_method(self.method_handler.method(flag, func))
            return wrapper
        return inner

    def accept_forever(self):
        host = self.config_mgr.get('host')
        port = self.config_mgr.get('port')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)

        logger.positive(f'binded to {host}:{port}')
        try:
            while True:
                cli_s, host = sock.accept()
                logger.positive(f'started connection with {host[0]}:{host[1]}')

                key_req = cli_s.recv(65535)
                pack = proto.packet.unbox(key_req)

                key_id = None
                key_pwd = None
                con = conn.connection(cli_s, key_id, key_pwd=key_pwd)
                self.conn_mgr.reg_conn(con)
        except KeyboardInterrupt:
            logger.negative(f'\nkeyboard interrupt')
            exit(1)
