

Neteye is a simple web database for network device, and a hub for network-to-code inspired by netmiko/scrapli/ntc-template.

## Features
1. Simple UI: Easily register and manage network device information with a simple and intuitive UI.
2. Incremental search: All tables support incremental search using DataTables. Quickly filter the information you need.
3. Command from the GUI: Execute commands from the GUI for each network device. No need to open a terminal for each device, connect via SSH, and execute a command.
4. Parsed command results: The output results of commands are output in table format if a corresponding ntc-template exists. You can also export to CSV, etc.
5. REST API: Provides an API that corresponds to each GUI operation. If you execute a command using the REST API, you can receive the result in JSON format if an ntc-template exists.
6. Versioning: All information about network devices, as well as the execution and output results of commands, are all tracked. You can check the past information and change history.

## Requirement
Python 3.7+ 

## Installation
``` shell
git clone https://github.com/yone2ks/neteye.git
cd neteye
pip install -r requirements.txt
git clone https://github.com/networktocode/ntc-templates.git
NET_TEXTFSM=./neteye/ntc-templates/ntc_templates/templates/ python manage.py
```

## Demo
![neteye-demo](https://github.com/yone2ks/neteye/assets/1281910/852a38d2-c1b3-45e0-abb6-a0858a2d610a)


## Configuration

## License
MIT 
## Author
yone2ks
