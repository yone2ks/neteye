import netmiko
from netmiko.ssh_autodetect import SSHDetect

class ConnectionPool():
    def __init__(self, pool_size=50):
        self.pool = {}
        self.pool_size = pool_size
        self.keepalive_time = 10

    def add_connection(self, params):
        try:
            params['keepalive'] = self.keepalive_time
            connection = netmiko.ConnectHandler(**params)
            self.pool[params['ip']] = connection
        except Exception as e:
            raise e

    def delete_connection(self, ip):
        self.pool[ip].disconnect()
        del self.pool[ip]

    def get_connection(self, ip):
        return self.pool[ip]

    def _connection_exists(self):
        return ip in self.pool

    def size(self):
        return len(self.pool)

