import netmiko
from netmiko.ssh_autodetect import SSHDetect

class ConnectionPool():
    def __init__(self, pool_size=50):
        self.pool = {}
        self.params_pool = {}
        self.pool_size = pool_size
        self.keepalive_time = 10

    def add_connection(self, params):
        try:
            params['keepalive'] = self.keepalive_time
            connection = netmiko.ConnectHandler(**params)
            self.pool[params['ip']] = connection
            self.params_pool[params['ip']] = params
        except Exception as e:
            raise e

    def delete_connection(self, ip):
        self.pool[ip].disconnect()
        del self.pool[ip]

    def recreate_connection(self, ip):
        connection = netmiko.ConnectHandler(**params)
        self.pool[params['ip']] = connection

    def get_connection(self, ip):
        if self.pool[ip].is_alive():
            return self.pool[ip]
        else:
            recreate_connection(ip)
            return self.pool[ip]

    def connection_exists(self, ip):
        return ip in self.pool

    def size(self):
        return len(self.pool)

