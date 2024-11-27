# Meshbook

A way to programmatically manage MeshCentral-managed machines, a bit like Ansible does.<br>
What problem does it solve? Well, what I wanted to be able to do is to automate system updates through [MeshCentral](https://github.com/ylianst/meshcentral).<br>
And many people will be comfortable with YAML configurations! It's almost like JSON, but different!<br>

# Quick-start:

The quickest way to start is to grab a template from the templates folder in this repository.<br>
Make sure to correctly pass the MeshCentral websocket API as `wss://<MeshCentral-Host>/control.ashx`.<br>
And make sure to fill in the credentails of an account which has remote commands permissions.<br>
Then make a yaml with a target and some commands! See below examples as a guideline. And do not forget to look at the bottom's notice.

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
python3 meshbook.py --playbook examples/ping.yaml --silent
3
Running task: {'name': 'Ping Cloudflare', 'command': 'ping 1.1.1.1 -c 4'}
-=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=--=-
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=6.74 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.41 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.53 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.55 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3005ms\nrtt min/avg/max/mdev = 6.412/6.555/6.736/0.116 ms\n",
    "responseid": "meshctrl",
    "nodeid": "<SECRET NODE-ID>"
}
1
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=6.12 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=57 time=6.05 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=57 time=5.89 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=57 time=6.00 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 5.887/6.013/6.119/0.084 ms\n",
    "responseid": "meshctrl",
    "nodeid": "<SECRET NODE-ID>"
}
2
{
    "action": "msg",
    "type": "runcommands",
    "result": "PING 1.1.1.1 (1.1.1.1) 56(84) bytes of data.\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=59 time=7.11 ms\n64 bytes from 1.1.1.1: icmp_seq=2 ttl=59 time=6.51 ms\n64 bytes from 1.1.1.1: icmp_seq=3 ttl=59 time=6.55 ms\n64 bytes from 1.1.1.1: icmp_seq=4 ttl=59 time=6.51 ms\n\n--- 1.1.1.1 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss, time 3004ms\nrtt min/avg/max/mdev = 6.508/6.670/7.113/0.255 ms\n",
    "responseid": "meshctrl",
    "nodeid": "<SECRET NODE-ID>"
}
0
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