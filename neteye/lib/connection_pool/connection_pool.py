from typing import NamedTuple


class ConnectionKey(NamedTuple):
    ip_address: str
    driver_type: str


class ConnectionAdaptor():
    connection: object
    driver_type: str

    def __init__(self, connection, driver_type):
        self.connection = connection
        self.driver_type = driver_type

    def is_alive(self):
        if self.driver_type == "napalm":
            return self.connection.is_alive()
        elif self.driver_type == "scrapli":
            return self.connection.isalive()
        else:
            return self.connection.is_alive()

    def close(self):
        if self.driver_type == "napalm":
            self.connection.close()
        elif self.driver_type == "scrapli":
            self.connection.close()
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
        connection_adaptor = ConnectionAdaptor(connection=node.gen_connection(driver_type), driver_type=driver_type)
        self.pool[connection_key] = connection_adaptor

    def get_connection(self, node, driver_type):
        connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
        if self.pool[connection_key].is_alive():
            return self.pool[connection_key].connection
        else:
            self.recreate_connection(node, driver_type)
            return self.pool[connection_key].connection

    def exists(self, node, driver_type):
        connection_key = ConnectionKey(ip_address=node.ip_address, driver_type=driver_type)
        return connection_key in self.pool

    def size(self):
        return len(self.pool)
