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
Running task: {'name': 'Ping Cloudflare', 'command': 'ping 1.1.1.1 -c 4'}
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.89 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.57 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.52 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.45 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 6.446/6.605/6.892/0.171 ms\n",
    "responseid": "meshctrl",
    "nodeid": "node//0fHMlKtmfVXhyHmJC09MWaIg0GZom$RVi9JffeTbbvKOx4AnTsfCJyQTiG4WYNIm"
}
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.27 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=5.96 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=5.96 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=6.29 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 5.963/6.122/6.292/0.159 ms\n",
    "responseid": "meshctrl",
    "nodeid": "node//QFq2o35$cHss2ELZnH6SnY@0JNbK1zXatZiUQ@JBcZlQcy8xi62b7R6iMfmfMaFL"
}
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.94 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.66 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.59 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.59 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 6.587/6.694/6.941/0.145 ms\n",
    "responseid": "meshctrl",
    "nodeid": "node//LJEX0zEOBTVZ@WDAArmURFRmXb3Puri0aQvb1GuYRPNA05S4u3EYrvBTKpQDn6jF"
}
Running task: {'name': 'Ping Google', 'command': 'ping 8.8.8.8 -c 4'}
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=5.61 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=5.22 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=5.23 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=118 time=5.33 ms\n\n--- 8.8.8.8 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.219/5.344/5.606/0.157 ms\n",
    "responseid": "meshctrl",
    "nodeid": "node//0fHMlKtmfVXhyHmJC09MWaIg0GZom$RVi9JffeTbbvKOx4AnTsfCJyQTiG4WYNIm"
}
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=5.63 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=5.35 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=5.55 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=118 time=5.42 ms\n\n--- 8.8.8.8 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 5.351/5.487/5.631/0.109 ms\n",
    "responseid": "meshctrl",
    "nodeid": "node//LJEX0zEOBTVZ@WDAArmURFRmXb3Puri0aQvb1GuYRPNA05S4u3EYrvBTKpQDn6jF"
}
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=4.86 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=4.76 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=4.74 ms\n64 bytes from 8.8.8.8: icmp_seq=4 ttl=118 time=4.71 ms\n\n--- 8.8.8.8 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3006ms\nrtt min/avg/max/mdev = 4.711/4.768/4.864/0.057 ms\n",
    "responseid": "meshctrl",
    "nodeid": "node//QFq2o35$cHss2ELZnH6SnY@0JNbK1zXatZiUQ@JBcZlQcy8xi62b7R6iMfmfMaFL"
}
```
Please ignore the module output in the example, I will remove that in a later version.

# Important Notice:

If you want to use this, make sure to use `NON-BLOCKING` commands. MeshCentral does not work if you send it commands that wait.<br>
A couple examples of `BLOCKING COMMANDS` which will never get back to the main MeshCentral server:

```shell
apt upgrade # without -y.

sleep infinity

ping 1.1.1.1 # without a -c flag (because it pings forever).
```
