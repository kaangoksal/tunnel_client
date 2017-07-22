import json
from Client.tasks.reverse_ssh_task import ReverseSSHTask

# TODO check whether start ssh task and stop ssh task was successful
# TODO look for possible try except use cases
# TODO think about return


class SshActionHandler(object):
    def __init__(self, settings):
        print("SSH Action Handler Started")
        self.active_ssh_tasks = {}
        self.key_location = settings["ssh_key_location"]
        self.server_addr = settings["ssh_server_addr"]
        self.server_username = settings["ssh_server_username"]

    def handle_message(self, message):
        """
        This method routes the message to the appropriate function
        :param message: SSH action message
        :return: result of the appropriate function
        """
        payload = json.loads(message.payload)
        action_type = payload["action_type"]
        parameters = json.loads(payload["parameters"])

        command = payload["command"]
        if command == "SSH-Start":
            return self.start_ssh_task(parameters)
        elif command == "SSH-Stop":
            return self.stop_ssh_task(parameters)
        else:
            print("Message Error SSH Action Handler " + str(message))
            return False

    def start_ssh_task(self, parameters):
        """
        This method starts the reverse ssh task
        :param parameters: the json object that the parameters are included
        :return: True if the task got created and started successfully false if something did not work
        """

        name = parameters["name"]
        local_port = parameters["local_port"]
        server_port = parameters["remote_port"]


        reverse_ssh_task = ReverseSSHTask(name, "starting",self.key_location, self.server_addr, self.server_username, local_port, server_port )

        # look whether it did start or not
        reverse_ssh_task.start_connection()
        self.active_ssh_tasks[name] = reverse_ssh_task

        return True


    def stop_ssh_task(self, parameters):
        """
        This method stops a certain reverse ssh task
        :param parameters:
        :return: successful or not
        """

        name = parameters["name"]
        # what if it doesnt exist?
        reverse_ssh_task = self.active_ssh_tasks[name]

        result = reverse_ssh_task.stop_connection()

        self.active_ssh_tasks.pop(name, None)
        # look whether the process was successful
        return True




