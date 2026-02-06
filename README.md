# Meshbook

[![CodeQL Advanced](https://github.com/DaanSelen/meshbook/actions/workflows/codeql.yaml/badge.svg)](https://github.com/DaanSelen/meshbook/actions/workflows/codeql.yaml)

> \[!NOTE]
> 💬 If you experience issues or have suggestions, [submit an issue](https://github.com/DaanSelen/meshbook/issues) — I'll respond ASAP!

Meshbook is a tool to **programmatically manage MeshCentral-managed machines**, inspired by tools like [Ansible](https://github.com/ansible/ansible).

## What problem does it solve?

Meshbook is designed to:

* Automate system updates or commands across multiple systems via [MeshCentral](https://github.com/Ylianst/MeshCentral), even behind third-party-managed firewalls.
* Allow configuration using simple and readable **YAML files** (like Ansible playbooks).
* Simplify the use of **group-based** or **tag-based** device targeting.

## 🏁 Quick Start

### ✅ Prerequisites

* Python 3
* Access to a MeshCentral instance and credentials with:

  * `Remote Commands`
  * `Details`
  * `Agent Console` permissions

A service account with access to the relevant device groups is recommended.

### 🔧 Installation

#### Linux

```bash
git clone https://github.com/daanselen/meshbook
cd ./meshbook
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
cp ./templates/api.conf.template ./api.conf
```

Next, make sure to fill in the following file:

```
nano ./api.conf
```

#### Windows (PowerShell)

```powershell
git clone https://github.com/daanselen/meshbook
cd .\meshbook
python -m venv .\venv
.\venv\Scripts\activate
pip install -r .\requirements.txt
cp .\templates\api.conf.template .\api.conf
```

Also here, make sure to fill in the `./api.conf` file.


> 📌 Rename `api.conf.template` to `api.conf` and fill in your actual connection details.
> The URL must start with `wss://<MeshCentral-Host>`.

> [!CAUTION]
> Negative potential consequences of an action.

## 🚀 Running Meshbook

Once installed and configured, run a playbook like this:

### Linux:

```bash
python3 meshbook.py -mb ./examples/echo_example.yaml
```

### Windows:

```powershell
.\venv\Scripts\python.exe .\meshbook.py -mb .\examples\echo_example.yaml
```

Use `--help` to explore available command-line options:

```bash
python3 meshbook.py --help
```

## 🛠️ Creating Configurations

Meshbook configurations are written in YAML. Below is an overview of supported fields.

### ▶️ Group Targeting (Primary*)

```yaml

name: My Configuration
group: "Dev Machines"
powershell: true
variables:
  - name: message
    value: "Hello from Meshbook"
tasks:
  - name: Echo a message
    command: 'echo "{{ message }}"'
```

* `group`: MeshCentral group (aka "mesh"). Quotation marks required for multi-word names.
* `powershell`: Set `true` for PowerShell commands on Windows clients.

### ▶️ Device Targeting (Secondary*)

You can also target a **specific device** rather than a group. See [`apt_update_example.yaml`](./examples/linux/apt_update_example.yaml) for reference.

### ▶️ Variables

Variables are replaced by Meshbook before execution. Syntax:

```yaml
variables:
  - name: example_var
    value: "Example value"

tasks:
  - name: Use the variable
    command: 'echo "{{ example_var }}"'
```

* Primary and Secondary mark the order in which will take prescendence

### ▶️ Tasks

Define multiple tasks:

```yaml
tasks:
  - name: Show OS info
    command: "cat /etc/os-release"
```

Each task must include:

* `name`: Description for human readability.
* `command`: The actual shell or PowerShell command.



## 🪟 Windows Client Notes

* Keep your `os_categories.json` up to date for proper OS filtering.
* Ensure Windows commands are compatible (use `powershell: true` if needed).
* Examples are available in [`examples/windows`](./examples/windows).



## 🔎 OS & Tag Filtering

### Filter by OS

You can limit commands to specific OS types:

```yaml
target_os: "Linux"  # As defined in os_categories.json
```

See [docs/operating\_system\_filtering.md](./docs/operating_system_filtering.md) for details.

### Filter by Tag

You can also filter using MeshCentral tags:

```yaml
target_tag: "Production"
```

> ⚠️ Tag values are **case-sensitive**.

## 📋 Example Playbook

```yaml

name: Echo OS Info
group: "Dev"
target_os: "Linux"
variables:
  - name: file
    value: "/etc/os-release"
tasks:
  - name: Show contents of os-release
    command: "echo $(cat {{ file }})"
```

Sample output:

```json
{
  "task 1": {
    "task_name": "Show contents of os-release",
    "data": [
      {
        "command": "echo $(cat /etc/os-release)",
        "result": [
          "NAME=\"Ubuntu\"",
          "VERSION=\"22.04.4 LTS (Jammy Jellyfish)\""
        ],
        "complete": true,
        "device_name": "dev-host1"
      }
    ]
  }
}
```

## ⚠ Blocking Commands Warning

Avoid using commands that **block indefinitely** — MeshCentral requires **non-blocking** execution.

🚫 Examples of bad (blocking) commands:

```bash
apt upgrade       # Without -y
sleep infinity    # Will never return
ping 1.1.1.1      # Without -c
```

✅ Use instead:

```bash
apt upgrade -y
sleep 3s
ping 1.1.1.1 -c 1
```



## 🧪 Check Python Environment

Sometimes the wrong Python interpreter or environment is used. To verify:

```bash
python3 -m pip list
pip3 list
```

The lists should match. If not, make sure the correct environment is activated.

## 📂 Project Structure (excerpt)

```bash
meshbook/
├── books/
│   ├── apt-update.yaml
│   └── rdp.yaml
├── examples/
│   ├── linux/
│   │   ├── apt_update_example.yaml
│   │   └── ...
│   └── windows/
│       ├── get_sys_info.yaml
│       └── ...
├── modules/
│   ├── executor.py
│   └── utilities.py
├── meshbook.py
├── os_categories.json
├── requirements.txt
├── templates/
│   └── api.conf.template
```

## 📄 License

This project is licensed under the terms of the GPL3 License. See [LICENSE](./LICENSE).
