from client.client_controller import ClientController
from client.client import CommunicationHandler
from client.handlers.message_handler import MessageHandler
from client.handlers.action_handler import ActionHandler
from client.handlers.ssh_action_handler import SshActionHandler


import configparser


def read_config():
    return_dict = {}
    config = configparser.ConfigParser()
    config.read("client_config")
    return_dict["server_addr"] = config.get("Tunnel Client Settings", "host")
    return_dict["server_port"] = int(config.get("Tunnel Client Settings", "port"))
    return_dict["username"] = config.get("Tunnel Client Settings", "username")
    return_dict["password"] = config.get("Tunnel Client Settings", "password")

    return_dict["ssh_key_location"] = config.get("SSH Task Settings", "key_location")
    return_dict["ssh_server_addr"] = config.get("SSH Task Settings", "server_addr")
    return_dict["ssh_server_username"] = config.get("SSH Task Settings", "server_username")
    return_dict["ssh_server_local_port"] = config.get("SSH Task Settings", "ssh_local_port")
    return_dict["ssh_server_remote_port"] = config.get("SSH Task Settings", "ssh_remote_port")

    return return_dict


if __name__ == '__main__':

    settings = read_config()

    communication_handler = CommunicationHandler(settings["server_port"],
                                                 settings["server_addr"],
                                                 settings["username"],
                                                 settings["password"])

    action_handler = ActionHandler()
    ssh_action_handler = SshActionHandler(settings)
    message_handler = MessageHandler(action_handler)

    client_controller = ClientController(communication_handler, message_handler)

    message_handler.server = client_controller
    action_handler.server = client_controller
    ssh_action_handler.server = client_controller

    action_handler.action_handlers["SSH"] = ssh_action_handler


    client_controller.run()
