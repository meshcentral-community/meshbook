> [!NOTE]
> *If you experience issues or have suggestions, submit an issue! https://github.com/DaanSelen/meshbook/issues I'll respond ASAP!*

# Meshbook

A way to programmatically manage MeshCentral-managed machines, inspired by applications like [Ansible](https://github.com/ansible/ansible).<br>
What problem does it solve? Well, what I wanted to be able to do is to automate system updates through [MeshCentral](https://github.com/ylianst/meshcentral). And some machines are behind unmanaged or 3rd party managed firewalls.<br>
And many people will be comfortable with YAML configurations! It's almost like JSON, but different!<br>

# Quick-start:

The quickest way to start is to grab a template from the templates folder in this repository.<br>
Make sure to correctly pass the MeshCentral websocket API as `wss://<MeshCentral-Host>`.<br>
And make sure to fill in the credentails of an account which has `Remote Commands`, `Details` and `Agent Console` permissions on the targeted devices or groups.<br>

> I did this through a "Service account" with rights on the device group.

Then make a yaml with a target and some commands! See below examples as a guideline. And do not forget to look at the bottom's notice.<br>
To install, follow the following commands:<br>

### Linux setup:

```bash
git clone https://github.com/daanselen/meshbook
cd ./meshbook
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r ./requirements.txt
cp ./templates/meshcentral.conf.template ./meshcentral.conf
```

### Windows setup (PowerShell, not cmd):

```shell
git clone https://github.com/daanselen/meshbook
cd ./meshbook
python -m venv ./venv # or python3 when done through the Microsoft Store.
.\venv\Scripts\activate # Make sure to check the terminal prefix.
pip3 install -r ./requirements.txt
cp .\templates\meshcentral.conf.template .\meshcentral.conf
```

Now copy the configuration template from ./templates and fill it in with the correct details (remove .template from the file) this is shown in the last step of the setup(s).<br>
The url should start with `wss://`.<br>
You can check pre-made examples in the examples directory, make sure the values are set to your situation.<br>
After this you can use meshbook, for example:

### Linux run:

```bash
python3 .\meshbook.py -pb .\examples\echo.yaml
```

### Windows run:

```shell
.\venv\Scripts\python.exe .\meshbook.py -pb .\examples\echo_example.yaml
```

### How to check if everything is okay?

The python virtual environment can get messed up, therefore...<br>
To check if everything is in working order, make sure that the lists from the following commands are aligned:

```
python3 -m pip list
pip3 list
```

If not, perhaps you are using the wrong executable, the wrong environment and so on...

# How to create a configuration?

This paragraph explains how the program interprets certain information.

### Targeting:

MeshCentral has `meshes` or `groups`, in this program they are called `group(s)`. Because of the way I designed this.<br>
So to target for example a mesh/group in MeshCentral called: "Nerthus" do:

> If your group has multiple words, then you need to use `"` to group the words.

```yaml
---
name: example configuration
group: "Nerthus"
#target_os: "Linux" # <--- according to os_categories.json
variables:
  - name: var1
    value: "This is the first variable"
tasks:
  - name: echo the first variable!
    command: 'echo "{{ var1 }}"'
```

It is also possible to target a single device, as seen in: [here](./examples/apt_update_example.yaml).<br>

### Variables:

Variables are done by replacing the placeholders just before the runtime (the Python program does this, not you).<br>
So if you have var1 declared, then the value of that declaration is placed wherever it finds {{ var1 }}.<br>
This is done to imitate popular methods. See below [from the example](./examples/variable_usage_example.yaml).<br>

### Tasks:

The tasks you want to run should be contained under the `tasks:` with two fields, `name` and `command`.<br>
The name field is for the user of meshbook, to clarify what the following command does in a summary.<br>
The command field actually gets executed on the end-point.<br>

### Granual Operating System filtering:

I have made the program so it can have a filter with the Operating systems. If you have a mixed group, please read:
[This explanation](./docs/operating_system_filtering.md)

# Example:

For the example, I used the following yaml file (you can find more in [this directory](./examples/)):

The below group: `Dev` has three devices, of which one is offline, Meshbook checks if the device is reachable.<br>
You can expand the command chain as follows:<br>

```yaml
---
name: Echo a string to the terminal through the meshbook example.
group: "Dev"
#target_os: "Linux" # <--- according to os_categories.json
variables:
  - name: file
    value: "/etc/os-release"
tasks:
  - name: Echo!
    command: "echo $(cat {{ file }})"
```

The following response it received when executing the first yaml of the above files (without the `-s` parameters, which just outputs the below JSON).

```shell
~/meshbook$ python3 meshbook.py -pb examples/echo_example.yaml
----------------------------------------
Playbook: examples/echo_example.yaml
Operating System Categorisation file: ./os_categories.json
Congiguration file: ./meshcentral.conf
Target group: Development
Grace: True
Silent: False
----------------------------------------
Trying to load the MeshCentral account credential file...
Trying to load the Playbook yaml file and compile it into something workable...
Trying to load the Operating System categorisation JSON file...
Connecting to MeshCentral and establish a session using variables from previous credential file.
Generating group list with nodes and reference the targets from that.
----------------------------------------
Executing playbook on the target(s): Development.
Initiating grace-period...
1...
2...
3...
----------------------------------------
1. Running: Echo!
----------------------------------------
{"Task 1": "ALL THE DATA"} # Not sharing due to PID
```
The above without `-s` is quite verbose. use `--help` to read about parameters and getting a minimal response for example.

# Important Notice:

If you want to use this, make sure to use `NON-BLOCKING` commands. MeshCentral does not work if you send it commands that wait.<br>
A couple examples of `BLOCKING COMMANDS` which will never get back to the main MeshCentral server, and Meshbook will quit after the timeout but the agent will not come back:

```shell
apt upgrade # without -y.

sleep infinity

ping 1.1.1.1 # without a -c flag (because it pings forever).
```
