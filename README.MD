**Version History**

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

