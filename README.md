

Neteye is a simple web database for network device, and a hub for network-to-code inspired by netmiko/scrapli/ntc-template.

## Features
1. Simple UI: Easily register and manage network device information with a simple and intuitive UI.
2. Incremental search: All tables support incremental search using DataTables. Quickly filter the information you need.
3. Command from the GUI: Execute commands from the GUI for each network device. No need to open a terminal for each device, connect via SSH, and execute a command.
4. Parsed command results: The output results of commands are output in table format if a corresponding ntc-template exists. You can also export to CSV, etc.
5. REST API: Provides an API that corresponds to each GUI operation. If you execute a command using the REST API, you can receive the result in JSON format if an ntc-template exists.
6. Versioning: All information about network devices, as well as the execution and output results of commands, are all tracked. You can check the past information and change history.

## Requirement
Python 3.8.17+ 

## Installation
``` shell
git clone https://github.com/yone2ks/neteye.git
cd neteye
pip install -r requirements.txt
git clone https://github.com/networktocode/ntc-templates.git
NET_TEXTFSM=./ntc-templates/ntc_templates/templates/ python manage.py
```

## Usage
### Device Registration
For Device Registration, input Hostname and IP Address, Password and so on. If Device Type is "autodetect", automatically device type is identified. 
![neteye_device_registration](https://github.com/yone2ks/neteye/assets/1281910/1a20797d-e374-4355-b59a-17b0c30f9234)

### Execute Command
Enter a command and click the "Command" button to execute the command on the device. If there is a corresponding ntc-template, the "Command" button returns the command result in a tabular format. "Command(Raw)"" button always returns the command result in plain text format. 
![neteye_execute_command](https://github.com/yone2ks/neteye/assets/1281910/fbb6f27b-e7e9-48bb-96bd-6ff34b593306)

### Import Device Infomaiton
Click "Import Node" button to import the device infomation(interface, serial, arp table).
![neteye_import_node](https://github.com/yone2ks/neteye/assets/1281910/f50b2b7e-d627-4562-bd14-6c885ae46a0e)

### History View
In "History" menu, you can check the history of device information and executed commands.


## Configuration

## License
MIT 
## Author
yone2ks
