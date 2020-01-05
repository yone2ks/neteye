import time
from netmiko_connection_pool import ConnectionPool

pool = ConnectionPool()
ip = "192.168.94.100"
params = {
    "device_type": "cisco_ios",
    "ip": "192.168.94.100",
    "username": "admin",
    "password": "cisco",
    "secret": "cisco",
}
pool.add_connection(params)
print("show ip arp")
print(pool.get_connection(ip).send_command("show ip arp"))
print("")
print("show inventory")
print(pool.get_connection(ip).send_command("show inventory"))
