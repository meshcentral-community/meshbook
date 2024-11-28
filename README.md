# Meshbook

A way to programmatically manage MeshCentral-managed machines, a bit like Ansible does.<br>
What problem does it solve? Well, what I wanted to be able to do is to automate system updates through [MeshCentral](https://github.com/ylianst/meshcentral).<br>
And many people will be comfortable with YAML configurations! It's almost like JSON, but different!<br>

# Quick-start:

The quickest way to start is to grab a template from the templates folder in this repository.<br>
Make sure to correctly pass the MeshCentral websocket API as `wss://<MeshCentral-Host>/control.ashx`.<br>
And make sure to fill in the credentails of an account which has remote commands permissions.<br>
Then make a yaml with a target and some commands! See below examples as a guideline. And do not forget to look at the bottom's notice.<br>
To install, follow the following commands:<br>

```shell
git clone https://github.com/daanselen/meshbook
cd ./meshbook
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r ./meshbook/requirements.txt
```
Then you can use meshbook, for example:
```shell
python3 ./meshbook/meshbook.py -pb examples/echo.yaml
```

# Example:

For the example, I used the following yaml file:

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
    value: "ns.systemec.nl"
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

The following response it received when executing the first yaml of the above files.

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
Running task: {'name': 'Ping host2', 'command': 'ping ns.systemec.nl -c 4'}
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
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.70 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.51 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.51 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.52 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 6.508/6.558/6.697/0.080 ms\n",
            "responseid": "meshctrl",
            "nodeid": "MSI"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.15 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=6.43 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=5.94 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=5.87 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.870/6.098/6.430/0.217 ms\n",
            "responseid": "meshctrl",
            "nodeid": "server"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.29 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=6.05 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=5.88 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=5.99 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 5.875/6.050/6.286/0.150 ms\n",
            "responseid": "meshctrl",
            "nodeid": "raspberrypi5"
        }
    ],
    "Batch 2": [
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING ns.systemec.nl (89.20.90.102) 56(84) bytes of data.\n64 bytes from roma.systemec.nl (89.20.90.102): icmp_seq=1 ttl=60 time=1.45 ms\n64 bytes from roma.systemec.nl (89.20.90.102): icmp_seq=2 ttl=60 time=1.10 ms\n64 bytes from roma.systemec.nl (89.20.90.102): icmp_seq=3 ttl=60 time=1.12 ms\n64 bytes from roma.systemec.nl (89.20.90.102): icmp_seq=4 ttl=60 time=1.14 ms\n\n--- ns.systemec.nl ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3003ms\nrtt min/avg/max/mdev = 1.100/1.199/1.448/0.143 ms\n",
            "responseid": "meshctrl",
            "nodeid": "raspberrypi5"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING ns.systemec.nl (89.20.90.102) 56(84) bytes of data.\n64 bytes from ns.systemec.nl (89.20.90.102): icmp_seq=1 ttl=59 time=1.52 ms\n64 bytes from ns.systemec.nl (89.20.90.102): icmp_seq=2 ttl=59 time=1.26 ms\n64 bytes from ns.systemec.nl (89.20.90.102): icmp_seq=3 ttl=59 time=1.34 ms\n64 bytes from ns.systemec.nl (89.20.90.102): icmp_seq=4 ttl=59 time=1.27 ms\n\n--- ns.systemec.nl ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3006ms\nrtt min/avg/max/mdev = 1.255/1.345/1.523/0.107 ms\n",
            "responseid": "meshctrl",
            "nodeid": "server"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING ns.systemec.nl (89.20.90.102) 56(84) bytes of data.\n64 bytes from ns.systemec.nl (89.20.90.102): icmp_seq=1 ttl=62 time=7.21 ms\n64 bytes from roma.systemec.nl (89.20.90.102): icmp_seq=2 ttl=62 time=0.346 ms\n64 bytes from ns.systemec.nl (89.20.90.102): icmp_seq=3 ttl=62 time=0.358 ms\n64 bytes from roma.systemec.nl (89.20.90.102): icmp_seq=4 ttl=62 time=0.336 ms\n\n--- ns.systemec.nl ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3018ms\nrtt min/avg/max/mdev = 0.336/2.061/7.205/2.969 ms\n",
            "responseid": "meshctrl",
            "nodeid": "MSI"
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
