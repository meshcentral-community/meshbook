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
cd ./meshbook
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```
Then you can use meshbook, for example:
```shell
python3 meshbook.py -pb examples/ping.yaml
```

# Example:

For the example, I used the following yaml file:

```yaml
---
name: Ping a single Point
company: Temp-Agents
tasks:
  - name: Ping Cloudflare
    command: "ping 1.1.1.1 -c 4"
```

The above group: `Temp-Agents` has four devices, of which one is offline.<br>
You can expand the command chain as follows:<br>

```yaml
---
name: Ping Multiple Points
company: Temp-Agents
tasks:
  - name: Ping Cloudflare
    command: "ping 1.1.1.1 -c 4"

  - name: Ping Google
    command: "ping 8.8.8.8 -c 4"
```

The following response it received when executing the first yaml of the above files.

```shell
python3 meshbook.py -pb examples/ping.yaml -s
{
    "Batch 1": [
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.88 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.50 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.46 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.51 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 6.460/6.588/6.879/0.169 ms\n",
            "responseid": "meshctrl",
            "nodeid": "MSI"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.22 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=6.07 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=5.97 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=5.90 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.904/6.038/6.216/0.117 ms\n",
            "responseid": "meshctrl",
            "nodeid": "server"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.83 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.64 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.65 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.53 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 6.534/6.664/6.834/0.108 ms\n",
            "responseid": "meshctrl",
            "nodeid": "raspberrypi5"
        }
    ],
    "Batch 2": [
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=5.69 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=5.22 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=5.19 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=118 time=5.16 ms\n\n--- 8.8.8.8 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.161/5.315/5.694/0.219 ms\n",
            "responseid": "meshctrl",
            "nodeid": "MSI"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=5.65 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=5.28 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=5.25 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=118 time=5.25 ms\n\n--- 8.8.8.8 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.246/5.357/5.648/0.168 ms\n",
            "responseid": "meshctrl",
            "nodeid": "raspberrypi5"
        },
        {
            "action": "msg",
            "type": "runcommands",
            "result": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=4.94 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=4.68 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=4.79 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=118 time=4.77 ms\n\n--- 8.8.8.8 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 4.678/4.792/4.940/0.094 ms\n",
            "responseid": "meshctrl",
            "nodeid": "server"
        }
    ]
}
```

# Important Notice:

If you want to use this, make sure to use `NON-BLOCKING` commands. MeshCentral does not work if you send it commands that wait.<br>
A couple examples of `BLOCKING COMMANDS` which will never get back to the main MeshCentral server:

```shell
apt upgrade # without -y.

sleep infinity

ping 1.1.1.1 # without a -c flag (because it pings forever).
```
