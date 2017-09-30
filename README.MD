**Version History**

V 0.0.19 (Future)
- Encrypt Communications
- Check server certificate

V 0.0.18 (Future)
- Send logs to the server
- Software update
- Automate key registeration + generation

V 0.0.17 (Future)
- Different message types and commands
- Agility cleanup
- Clean up timings

V 0.0.16 (Future)
- Seperate processes for actions
- Solved reconnection problem due to a race condition

V 0.0.15 (Deployed Beta)
- Client sends the ping to the server
- Client tries to establish a new connection if it does not receive a reply

V 0.0.12
- Replies to ping 

V 0.0.1
- Improved status message check for reverse ssh task
- Added software version


**Setup Instructions**

add this to the /etc/rc.local file

`cd /home/pi/centree_tunnel_client`  
`screen -d -m -s /bin/bash python3 main.py`  

add the ssh key located in the resources folder to /home/pi/.ssh/ folder  

execute this command once to get the server fingerprint on the client  
`ssh -N -R 7002:localhost:22 -i /home/pi/.ssh/ssh_server_key ssh_server@backend.centree.xyz`


**Commands**

PING Message
{  
    "payload": "{\"utility_type\": \"PING\"}",  
    "sender": "server",  
    "to": "floatingPi",  
    "type": "utility"  
}  

when the client receives the ping message it replies with ping,

{  
    "payload": "ping reply",  
    "sender": "floatingPi",  
    "to": "server",  
    "type": "utility"  
}

This ensures that the tcp conenction remains open! wo la! 

REVERSE SSH
{
    "payload": "{\"parameters\": \"{\\\"remote_port\\\": 7005, \\\"name\\\": \\\"shell connection\\\", \\\"local_port\\\": 22}\", \"action_type\": \"SSH\", \"command\": \"SSH-Start\"}",
    "sender": "server",
    "to": "floatingPi",
    "type": "action"
}

after this message if the client can start the reverse ssh successfully it returns

{
    "payload": "SSH Started Port 7005",
    "sender": "floatingPi",
    "to": "server",
    "type": "result"
}

STOP
{
    "payload": "{\"parameters\": \"{\\\"name\\\": \\\"shell connection\\\"}\", \"action_type\": \"SSH\", \"command\": \"SSH-Stop\"}",
    "sender": "server",
    "to": "floatingPi",
    "type": "action"
}

result

{
    "payload": "SSH Stopped name shell connection",
    "sender": "floatingPi",
    "to": "server",
    "type": "result"
}






