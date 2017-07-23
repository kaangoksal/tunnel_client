import json
from client.tasks.reverse_ssh_task import ReverseSSHTask
from Message import Message

# TODO check whether start ssh task and stop ssh task was successful
# TODO look for possible try except use cases
# TODO think about return


class SshActionHandler(object):
    def __init__(self, settings, server=None):
        """
        constructor of sshAction handler
        :param settings: the settings dictionary which will have the default settings for the ssh task
        :param server: the server object which we can do shit according to messages and states
        """
        print("SSH Action Handler Started")
        self.server = server
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

        reverse_ssh_task = ReverseSSHTask(name,
                                          "starting",
                                          self.key_location,
                                          self.server_addr,
                                          self.server_username,
                                          local_port,
                                          server_port)

        # look whether it did start or not
        successful, message = reverse_ssh_task.start_connection()
        print(successful)
        print(message)
        if successful:
            self.active_ssh_tasks[name] = reverse_ssh_task
            result_message = Message(self.server.communication_handler.username, "server", "result",
                                     "SSH Started " + "Port " + str(reverse_ssh_task.remote_port))

            self.server.outbox_queue.put(result_message)

            print(self.active_ssh_tasks)

        elif not successful:
            result_message = Message(self.server.communication_handler.username, "server", "result",
                                     "SSH Problem " + str(message))
            self.server.outbox_queue.put(result_message)


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

        result_message = Message(self.server.communication_handler.username, "server", "result",
                                 "SSH Stopped " + "name " + str(name))

        self.server.outbox_queue.put(result_message)

        return True




