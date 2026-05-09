Neteye is a simple web database for network devices, and a hub for network-to-code inspired by netmiko/scrapli/ntc-templates.

## Features
1. Simple UI: Easily register and manage network device information with a simple and intuitive UI.
2. Incremental search: All tables support incremental search using DataTables. Quickly filter the information you need.
3. Command from the GUI: Execute commands from the GUI for each network device. No need to open a terminal for each device, connect via SSH, and execute a command.
4. Parsed command results: Command output is displayed in table format when a matching ntc-template exists. Results can be exported to CSV.
5. REST API: Provides an API corresponding to each GUI operation. Command results are returned in JSON format when an ntc-template exists.
6. Versioning: All network device information, command execution history, and output results are tracked. You can review past data and change history.

## Requirements
Python 3.10+

## Installation

```shell
git clone https://github.com/yone2ks/neteye.git
cd neteye
pip install -r requirements.txt

# Set up ntc-templates (for parsed command output)
git clone https://github.com/networktocode/ntc-templates.git

# Copy and edit the environment file
cp .env.example .env
# Edit .env and fill in SECRET_KEY, SECURITY_PASSWORD_SALT, ADMIN_PASSWORD, etc.

# Start the application
python manage.py
```

The application will be available at `http://localhost:5001`.
Default admin credentials: email `neteye_admin@yourcompany.com`, password as set in `NETEYE_ADMIN_PASSWORD`.

## Configuration

Neteye uses two configuration files with different responsibilities:

| File | Purpose | Committed to git |
|------|---------|-----------------|
| `.env` | Secrets and per-environment values (passwords, keys) | No — git-ignored |
| `settings.toml` | Application behaviour (timeouts, ports, limits) | Yes |

As a rule of thumb: if a value would be a security risk if leaked, put it in `.env`. Everything else goes in `settings.toml`.

### Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in the values. This file is git-ignored and must never be committed.

| Variable | Description |
|----------|-------------|
| `NETEYE_SECRET_KEY` | Flask session encryption key (use a long random string) |
| `NETEYE_SECURITY_PASSWORD_SALT` | Salt for password hashing (use a long random string) |
| `NETEYE_ADMIN_PASSWORD` | Initial administrator password |
| `NETEYE_DISCOVERY_CREDENTIALS__N__USERNAME` | Username for network discovery auto-connect (N=1,2,3,...) |
| `NETEYE_DISCOVERY_CREDENTIALS__N__PASSWORD` | Password for network discovery auto-connect |
| `NETEYE_DISCOVERY_CREDENTIALS__N__ENABLE` | Enable password for network discovery auto-connect |
| `NET_TEXTFSM` | Absolute path to the ntc-templates `templates/` directory |

### Application Settings (`settings.toml`)

Main application behaviour is configured in `settings.toml`. Key settings are listed below.

| Key | Default | Description |
|-----|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5001` | Server port |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:////var/tmp/neteye.db` | Database path. ⚠️ `/var/tmp` is cleared on reboot — change this for production use |
| `CUSTOM_TEMPLATES_DIR` | `''` | Absolute path to custom ntc-templates directory. Leave empty to disable |
| `NETMIKO_CONN_TIMEOUT` | `1` | SSH connection timeout in seconds |
| `NETMIKO_READ_TIMEOUT` | `10` | SSH read timeout in seconds |
| `NAPALM_TIMEOUT` | `1` | NAPALM connection timeout in seconds |
| `COMMAND_HISTORY_MAX_RECORDS` | `10000` | Max command history records kept in DB (0 = unlimited) |
| `ARP_ENTRY_HISTORY_MAX_RECORDS` | `50000` | Max ARP entry history records (0 = unlimited) |
| `AUTO_DETECT_DEVICE_TYPES` | (list) | Device types targeted by netmiko autodetect |

Environment-specific overrides can be added under `[development]`, `[production]`, or `[testing]` sections in `settings.toml`. Set the `ENV_FOR_DYNACONF` environment variable to switch environments (default: `development`).

```shell
ENV_FOR_DYNACONF=production python manage.py
```

Note: `.env` is a flat `KEY=VALUE` file with no environment sections — it is always loaded regardless of the active environment. Use it only for secrets that must not be committed. All other environment-specific values (timeouts, limits, etc.) belong in the appropriate section of `settings.toml`.

## Usage

### Device Registration
Register a network device by entering its hostname, IP address, credentials, and device type. If Device Type is set to `autodetect`, the device type is identified automatically via netmiko's SSH fingerprinting.

![neteye_device_registration](https://github.com/yone2ks/neteye/assets/1281910/1a20797d-e374-4355-b59a-17b0c30f9234)

### Execute Command
Enter a command and click **Command** to execute it on the device. When a matching ntc-template exists, results are displayed in a structured table. **Command (Raw)** always returns plain text output.

![neteye_execute_command](https://github.com/yone2ks/neteye/assets/1281910/fbb6f27b-e7e9-48bb-96bd-6ff34b593306)

### Import Device Information
Click **Import Node** to pull the device's interface list, serial numbers, and ARP table into the database.

![neteye_import_node](https://github.com/yone2ks/neteye/assets/1281910/f50b2b7e-d627-4562-bd14-6c885ae46a0e)

### Network Discovery
Send a POST request to `/node/<id>/discover_node` to automatically discover neighboring devices via the node's ARP table. Neteye attempts SSH connections using the credentials defined in `NETEYE_DISCOVERY_CREDENTIALS` and registers reachable devices.

### History View
The **History** menu shows the change history of device information and a log of all executed commands.

## REST API

Neteye provides a REST API for all major operations.

**Authentication**

Obtain a token by posting credentials to the login endpoint:

```shell
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "neteye_admin@yourcompany.com", "password": "your-password"}'
```

Include the token in subsequent requests:

```
Authentication-Token: <token>
```

Tokens expire after 7 days (`SECURITY_TOKEN_MAX_AGE = 604800`).

**Swagger UI**

Interactive API documentation is available at:
```
http://localhost:5001/api/
```

**Main Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/nodes` | List all nodes |
| `POST` | `/api/nodes` | Create a node |
| `GET` | `/api/nodes/<id>` | Get a node |
| `PUT` | `/api/nodes/<id>` | Update a node |
| `DELETE` | `/api/nodes/<id>` | Delete a node |
| `GET` | `/api/nodes/<id>/command/<command>` | Execute command (parsed) |
| `GET` | `/api/nodes/<id>/raw_command/<command>` | Execute command (raw) |
| `POST` | `/api/nodes/<id>/import/all_data` | Import all device data |
| `GET` | `/api/interfaces` | List all interfaces |
| `GET` | `/api/serials` | List all serials |

## License
MIT

## Author
yone2ks
