Neteye is a simple web database for network devices, and a hub for network-to-code inspired by netmiko/scrapli/ntc-templates.

## Background

Managing network devices in the 2020s still means opening a terminal for each device, running commands, and reading raw text output. Commercial tools that automate configuration collection exist, but they are expensive and often overkill for smaller operations. Meanwhile, REST APIs are increasingly common on modern devices, yet many critical pieces of information are still only accessible via CLI commands.

Neteye was built to close these gaps:

- **One place, every device** — no more jumping between terminals; manage and operate all devices from a single web UI.
- **Human-readable output** — command results are rendered as sortable, filterable tables instead of raw text, making them far easier to read and act on.
- **Lightweight, open-source alternative** — self-host it without licensing costs, without the complexity of enterprise solutions.
- **Structured data from CLI** — commands that have no API equivalent are parsed via ntc-templates and exposed through a REST API, turning CLI output into structured JSON and pushing network-to-code forward.

## Features
1. Simple UI: Easily register and manage network device information with a simple and intuitive UI.
2. Incremental search: All tables support incremental search using DataTables. Quickly filter the information you need.
3. Command from the GUI: Execute commands from the GUI for each network device. No need to open a terminal for each device, connect via SSH, and execute a command.
4. Parsed command results: Command output is displayed in table format when a matching ntc-template exists. Results can be exported to CSV.
5. REST API: Provides an API corresponding to each GUI operation. Command results are returned in JSON format when an ntc-template exists.
6. Versioning: All network device information, command execution history, and output results are tracked. You can review past data and change history.
7. Import: Automatically fetch interface lists, serial numbers, and ARP tables from a device over SSH and store them in the database with a single click.
8. Ping (Preview): Execute ping from a network device via the GUI and view results in real time.
9. Traceroute (Preview): Execute traceroute from a network device via the GUI and view hop-by-hop results in real time.

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

Neteye uses three configuration files with different responsibilities:

| File | Purpose | Committed to git |
|------|---------|-----------------|
| `.env` | Secrets (passwords, keys) | No — git-ignored |
| `settings.toml` | Application defaults | Yes — do not edit directly |
| `settings.local.toml` | Local overrides | No — git-ignored |

As a rule of thumb: if a value would be a security risk if leaked, put it in `.env`. For local customisations (DB path, timeouts, etc.), use `settings.local.toml`. The `settings.toml` file contains shared defaults and should not be edited directly — it may be updated by `git pull`.

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

### Application Settings (`settings.toml` / `settings.local.toml`)

`settings.toml` contains application defaults and is managed by git. To override values for your environment, create `settings.local.toml` in the same directory — it is git-ignored and will never be overwritten by `git pull`.

Example `settings.local.toml`:

```toml
[default]
SQLALCHEMY_DATABASE_URI = "sqlite:////home/user/neteye.db"
NETMIKO_CONN_TIMEOUT = 5
NETMIKO_READ_TIMEOUT = 30
```

Key settings and their defaults:

| Key | Default | Description |
|-----|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5001` | Server port |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:////var/tmp/neteye.db` | Database path. ⚠️ `/var/tmp` is cleared on reboot — override in `settings.local.toml` for production use |
| `CUSTOM_TEMPLATES_DIR` | `''` | Absolute path to custom ntc-templates directory. Leave empty to disable |
| `NETMIKO_CONN_TIMEOUT` | `1` | SSH connection timeout in seconds |
| `NETMIKO_READ_TIMEOUT` | `10` | SSH read timeout in seconds |
| `NAPALM_TIMEOUT` | `1` | NAPALM connection timeout in seconds |
| `COMMAND_HISTORY_MAX_RECORDS` | `10000` | Max command history records kept in DB (0 = unlimited) |
| `ARP_ENTRY_HISTORY_MAX_RECORDS` | `50000` | Max ARP entry history records (0 = unlimited) |
| `AUTO_DETECT_DEVICE_TYPES` | (list) | Device types targeted by netmiko autodetect |

Environment-specific overrides can be added under `[development]`, `[production]`, or `[testing]` sections in `settings.toml` or `settings.local.toml`. Set the `ENV_FOR_DYNACONF` environment variable to switch environments (default: `development`).

```shell
ENV_FOR_DYNACONF=production python manage.py
```

Note: `.env` is a flat `KEY=VALUE` file with no environment sections — it is always loaded regardless of the active environment. Use it only for secrets that must not be committed.

## Usage

### Device Registration
Register a network device by entering its hostname, IP address, credentials, and device type. If Device Type is set to `autodetect`, the device type is identified automatically via netmiko's SSH fingerprinting.

https://github.com/user-attachments/assets/9ad0afd1-ce86-4020-b71f-ef6aada7de57

### Execute Command
Enter a command and click **Command** to execute it on the device. When a matching ntc-template exists, results are displayed in a structured table. **Command (Raw)** always returns plain text output.

https://github.com/user-attachments/assets/830b55cb-f88a-4c12-89c4-bcf171af8d92

### Import Device Information
Click **Import All Data** to pull the device's interface list, serial numbers, and ARP table into the database.

https://github.com/user-attachments/assets/f209fee1-e170-4028-b701-6152659f4431

### History View
The **History** menu shows the change history of device information and a log of all executed commands.

### Troubleshoot (Preview)
The **Troubleshoot** menu provides real-time network diagnostic tools executed directly from a registered device.

- **Ping** (`/troubleshoot/ping`): Send ping from a selected source node to a destination IP. Output streams live via Server-Sent Events. Supports source interface, VRF, packet count, timeout, and data size.

https://github.com/user-attachments/assets/72ce72e7-3801-418b-9c0e-43b0767cf719


- **Traceroute** (`/troubleshoot/traceroute`): Run traceroute from a selected source node. Each hop appears as it is received. Supports source interface, VRF, max TTL, probe count, and timeout. Known IP addresses are automatically annotated with their hostname or interface name.

https://github.com/user-attachments/assets/cc7c7215-de67-4e0d-8da6-f48a2ce34ffa

Both tools record execution history to the **Command History** log.



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
MIT — see [LICENSE](LICENSE) for details.

## Author
yone2ks
