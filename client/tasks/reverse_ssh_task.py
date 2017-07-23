import subprocess
import time
import os
import signal
import select

"""
How does this shit work?
Well... good question.

When the command gets executed, a reverse ssh tunnel is created to the server at umb.kaangoksal.com
starting at the port 7000 on the server and at 22 on the client (the computer which executes this code)
-N allows us to not to start a ssh shell to the remote pc, if you remove that it will ssh into ssh_server@umb.kaangoksal.com

The ssh_server user is a non sudo user, therefore even you access the server with that account you cant do much. (This will also be patched...)



To start the reverse ssh thing, I have used the default ssh server/client, running on linux machines. This is the best way to make sure that it is secure.
The shell command for reverse ssh is executed with subprocess and then it can be killed with os.killpg(os.getpgid(cmd.pid), signnal.SIGTERM). However you need to
start the process in a way that it will take down the child process created by the command. When subprocess command executes, two processes start

kaan     20155 20154  0 13:00 ?        00:00:00 /bin/sh -c ssh -N -R 7000:localhost:22 -i /home/kaan/Desktop/centree-clientsupervisor/ssh_server_key ssh_server@umb.kaangoksal.com
kaan     20156 20155  0 13:00 ?        00:00:00 ssh -N -R 7000:localhost:22 -i /home/kaan/Desktop/centree-clientsupervisor/ssh_server_key ssh_server@umb.kaangoksal.com

you might kill one of them but if the other one is not killed (with the pid 20155) the reverse ssh connection will be left open!



ssh -N -R 7002:localhost:22 -i /home/pi/.ssh/ssh_server_key ssh_server@backend.centree.xyz
The authenticity of host 'backend.centree.xyz (52.5.178.171)' can't be established.
ECDSA key fingerprint is cd:8a:72:d7:d9:a8:71:c3:10:db:a2:f1:7c:fa:dd:fd.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added 'backend.centree.xyz,52.5.178.171' (ECDSA) to the list of known hosts.


root@raspberrypi:/home/pi# ssh -N -R 7002:localhost:22 -i /home/pi/.ssh/ssh_server_key ssh_server@backend.centree.xyz
The authenticity of host 'backend.centree.xyz (52.5.178.171)' can't be established.
ECDSA key fingerprint is cd:8a:72:d7:d9:a8:71:c3:10:db:a2:f1:7c:fa:dd:fd.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added 'backend.centree.xyz,52.5.178.171' (ECDSA) to the list of known hosts.



Sources:
https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612


"""
#TODO fix the host error which requires manual reverse ssh connection initially


class ReverseSSHTask(object):
    def __init__(self, name, status, key_location, server_addr, server_username, localport, remoteport):
        self.name = name
        self.status = status
        self.key_location = key_location
        self.server_addr = server_addr
        self.server_username = server_username
        self.local_port = localport
        self.remote_port = remoteport

        self.ssh_process = None

    def start_connection(self):
        """
        This method starts the reverse ssh connections
        :return: True if it was a success False if it is failed!
        """
        command = "ssh -N -R " + str(self.remote_port) + ":localhost:" + str(
            self.local_port) + " -i " + self.key_location + " " + self.server_username + "@" + self.server_addr
        try:
            self.ssh_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                                preexec_fn=os.setsid)
            # read the stdout and stderr for possible errors
            turns = 0
            while 1:
                readable, writable, e = select.select([self.ssh_process.stdout, self.ssh_process.stderr], [], [], 1)
                if len(readable) > 0:
                    return_message = ""
                    for pipe in readable:
                        output = b''
                        byte_read = None
                        while byte_read != b'':
                            byte_read = pipe.read(1)
                            output += byte_read
                        return_message += output.decode("utf-8")
                    return False, return_message
                elif turns > 5:
                    # we can also check ps -ef | grep ssh
                    return True, None
                else:
                    time.sleep(1)
                    turns += 1

        except Exception as e:
            print("Failed Starting reverse SSH " + str(e))
            return False, str(e)

    def stop_connection(self):
        """
        This stops the ssh connection by terminating it. It blocks about 5 seconds to check whether it terminated for sure.
        :return:
        """
        # Don't forget that we are killing the group processes not only one of them.
        os.killpg(os.getpgid(self.ssh_process.pid), signal.SIGTERM)
        time.sleep(5)
        if self.get_status():
            # if it is still working
            os.killpg(os.getpgid(self.ssh_process.pid), signal.SIGKILL)

    def get_status(self):
        """
        This method polls whether the process is still running, not to forget this does not ensure that
        ssh connection is healthy or up... It just check whether the process that started it is still working
        this can mean that ssh is still up... To debug you can ps -ef | grep ssh
        :return: whether reverse ssh process is still up. True if it is up False if it is down.
        """
        # TODO might give more details about why it is not working!
        if self.ssh_process.poll() is None:
            # This means that the process is working
            return True
        else:
            return False
