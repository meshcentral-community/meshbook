> [!NOTE]
> *If you experience issues or have suggestions, submit an issue! https://github.com/DaanSelen/meshbook/issues I'll respond ASAP!*

# Meshbook

A way to programmatically manage MeshCentral-managed machines, a bit like Ansible does.<br>
What problem does it solve? Well, what I wanted to be able to do is to automate system updates through [MeshCentral](https://github.com/ylianst/meshcentral).<br>
And many people will be comfortable with YAML configurations! It's almost like JSON, but different!<br>

# Quick-start:

The quickest way to start is to grab a template from the templates folder in this repository.<br>
Make sure to correctly pass the MeshCentral websocket API as `wss://<MeshCentral-Host>/control.ashx`.<br>
And make sure to fill in the credentails of an account which has `Remote Commands` permissions and `Device Details` permissions on the targeted devices or groups.<br>

> I did this through a "Global Service" group which I added the meshbook account to!

Then make a yaml with a target and some commands! See below examples as a guideline. And do not forget to look at the bottom's notice.<br>
To install, follow the following commands:<br>

### Linux setup:

```shell
git clone https://github.com/daanselen/meshbook
cd ./meshbook
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r ./meshbook/requirements.txt
```

### Windows setup:

```shell
git clone https://github.com/daanselen/meshbook
cd ./meshbook
python3 -m venv ./venv
.\venv\Scripts\activate # Make sure to check the terminal prefix.
pip3 install -r ./meshbook/requirements.txt
```

Now copy the configuration template from ./templates and fill it in with the correct details. The url should start with `wss://` and end in `control.ashx`.<br>
After this you can use meshbook, for example:

### Linux run:

```shell
python3 .\meshbook\meshbook.py -pb .\examples\echo.yaml
```

### Windows run:

```shell
.\venv\Scripts\python.exe .\meshbook\meshbook.py -pb .\examples\echo.yaml
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

MeshCentral has `meshes` or `groups`, in this program they are called `companies`. Because of the way I designed this.<br>
So to target for example a mesh/group in MeshCentral called: "Nerthus" do:

> If your group has multiple words, then you need to use `"` to group the words.

```yaml
---
name: example configuration
company: "Nerthus"
variables:
  - name: var1
    value: "This is the first variable"
tasks:
  - name: echo the first variable!
    command: 'echo "{{ var1 }}"'
```

It is also possible to target a single device, as seen in: [here](./examples/echo.yaml).<br>

### Variables:

Variables are done by replacing the placeholders just before the runtime.<br>
So if you have var1 declared, then the value of that declaration is placed wherever it finds {{ var1 }}.<br>
This is done to imitate popular methods. See below [from the example](./examples/variable_example.yaml).<br>

### Tasks:

The tasks you want to run should be contained under the `tasks:` with two fields, `name` and `command`.<br>
The name field is for the user of meshbook, to clarify what the following command does in a summary.<br>
The command field actually gets executed on the end-point.<br>

# Example:

For the example, I used the following yaml file (you can find more in [this directory](./examples/)):

The below group: `Temp-Agents` has four devices, of which one is offline.<br>
You can expand the command chain as follows:<br>

```yaml
---
name: Ping Multiple Points
company: Temp-Agents
variables:
  - name: host1
    value: "1.1.1.1"
  - name: host2
    value: "9.9.9.9"
  - name: command1
    value: "ping"
  - name: cmd_arguments
    value: "-c 4"
tasks:
  - name: Ping host1
    command: "{{ command1 }} {{ host1 }} {{ cmd_arguments }}"

  - name: Ping host2
    command: "{{ command1 }} {{ host2 }} {{ cmd_arguments }}"
```

The following response it received when executing the first yaml of the above files (with the `-s` and the `-i` parameters).

```shell
python3 meshbook/meshbook.py -pb examples/variable_example.yaml -si
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
Running task: {'name': 'Ping host1', 'command': 'ping 1.1.1.1 -c 4'}
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
Current Batch: 1
Current response number: 1
Current Calculation: 1 % 3 = 1
Current Batch: 1
Current response number: 2
Current Calculation: 2 % 3 = 2
Current Batch: 1
Current response number: 3
Current Calculation: 3 % 3 = 0
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
Running task: {'name': 'Ping host2', 'command': 'ping 9.9.9.9 -c 4'}
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
Current Batch: 2
Current response number: 4
Current Calculation: 4 % 3 = 1
Current Batch: 2
Current response number: 5
Current Calculation: 5 % 3 = 2
Current Batch: 2
Current response number: 6
Current Calculation: 6 % 3 = 0
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
{
    "Batch 1": [
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.73 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.37 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.31 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.44 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 6.312/6.461/6.727/0.159 ms\n",
            "responseid": "meshctrl",
            "nodeid": "MSI"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.18 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=6.17 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=6.17 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=6.27 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 6.170/6.200/6.274/0.042 ms\n",
            "responseid": "meshctrl",
            "nodeid": "raspberrypi5"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.33 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=6.13 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=5.92 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=5.91 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 5.908/6.072/6.334/0.173 ms\n",
            "responseid": "meshctrl",
            "nodeid": "server"
        }
    ],
    "Batch 2": [
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 9.9.9.9 (9.9.9.9) 56(84) bytes of data.\n64 bytes from 9.9.9.9: icmp_seq=1 ttl=61 time=10.4 ms\n64 bytes from 9.9.9.9: icmp_seq=2 ttl=61 time=9.96 ms\n64 bytes from 9.9.9.9: icmp_seq=3 ttl=61 time=9.83 ms\n64 bytes from 9.9.9.9: icmp_seq=4 ttl=61 time=9.96 ms\n\n--- 9.9.9.9 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 9.830/10.036/10.396/0.214 ms\n",
            "responseid": "meshctrl",
            "nodeid": "MSI"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 9.9.9.9 (9.9.9.9) 56(84) bytes of data.\n64 bytes from 9.9.9.9: icmp_seq=1 ttl=60 time=10.8 ms\n64 bytes from 9.9.9.9: icmp_seq=2 ttl=60 time=10.6 ms\n64 bytes from 9.9.9.9: icmp_seq=3 ttl=60 time=10.5 ms\n64 bytes from 9.9.9.9: icmp_seq=4 ttl=60 time=10.5 ms\n\n--- 9.9.9.9 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 10.450/10.593/10.773/0.118 ms\n",
            "responseid": "meshctrl",
            "nodeid": "raspberrypi5"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 9.9.9.9 (9.9.9.9) 56(84) bytes of data.\n64 bytes from 9.9.9.9: icmp_seq=1 ttl=59 time=10.8 ms\n64 bytes from 9.9.9.9: icmp_seq=2 ttl=59 time=10.6 ms\n64 bytes from 9.9.9.9: icmp_seq=3 ttl=59 time=10.9 ms\n64 bytes from 9.9.9.9: icmp_seq=4 ttl=59 time=10.7 ms\n\n--- 9.9.9.9 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3006ms\nrtt min/avg/max/mdev = 10.600/10.750/10.898/0.117 ms\n",
            "responseid": "meshctrl",
            "nodeid": "server"
        }
    ]
}
All tasks completed successfully: Expected 6 Received 6
```
The above with `-si` is quite verbose. use `--help` to read about parameters.

# Important Notice:

If you want to use this, make sure to use `NON-BLOCKING` commands. MeshCentral does not work if you send it commands that wait.<br>
A couple examples of `BLOCKING COMMANDS` which will never get back to the main MeshCentral server:

```shell
apt upgrade # without -y.

sleep infinity

ping 1.1.1.1 # without a -c flag (because it pings forever).
```
