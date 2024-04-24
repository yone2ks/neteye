from typing import NamedTuple
from ssh2.exceptions import SocketRecvError, SocketSendError, Timeout, ChannelEOFSentError
from scrapli.exceptions import ScrapliConnectionNotOpened

class ConnectionKey(NamedTuple):
    ip_address: str
    driver_type: str


class ConnectionAdaptor():
    connection: object
    driver_type: str

    def __init__(self, connection, driver_type):
        self.connection = connection
        self.driver_type = driver_type

    def is_alive(self):         # netmiko/sdrapli/naplam's is_alive method is not working
        try:
            if self.driver_type == "napalm":
                self.connection.cli(['\n'])
                return True
            elif self.driver_type == "scrapli":
                self.connection.send_command('\n', timeout_ops=2)
                return True
            else:
                self.connection.send_command('\n', delay_factor=4)
                return True
        except (SocketRecvError, SocketSendError, Timeout, ChannelEOFSentError, ScrapliConnectionNotOpened, BrokenPipeError, OSError):
            return False

    def close(self):
        if self.driver_type == "napalm":
            self.connection.close()
        elif self.driver_type == "scrapli":
            try:
                self.connection.close()
            except SocketRecvError:
                self.connection.transport.close()
                self.connection.channel.close()
        else:
            self.connection.disconnect()


class ConnectionPool:
    def __init__(self, pool_size=50):
        self.pool = {}
        self.pool_size = pool_size

    def add_connection(self, node, driver_type):
        try:
            connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
            connection_adaptor = ConnectionAdaptor(connection=node.gen_connection(driver_type), driver_type=driver_type)
            self.pool[connection_key] = connection_adaptor
        except Exception as err:
            raise err

    def delete_connection(self, node, driver_type):
        connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
        connection_adaptor = self.pool.pop(connection_key)
        connection_adaptor.close()

    def recreate_connection(self, node, driver_type):
        connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
        if self.pool[connection_key].is_alive():
            self.delete_connection(node, driver_type)
        self.add_connection(node, driver_type)

    def get_connection(self, node, driver_type):
        connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
        if self.pool[connection_key].is_alive():
            return self.pool[connection_key].connection
        else:
            self.add_connection(node, driver_type)
            return self.pool[connection_key].connection

    def exists(self, node, driver_type):
        connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
        return connection_key in self.pool

    def size(self):
        return len(self.pool)
