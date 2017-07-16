from Client.client_controller import ClientController
from Client.client import Client
from Client.tasks.reverse_ssh_task import ReverseSSHTask
import configparser

def readConfig():
    return_dict = {}
    Config = configparser.ConfigParser()
    Config.read("client_config")
    return_dict["server_addr"] = Config.get("Tunnel Client Settings", "host")
    return_dict["server_port"] = int(Config.get("Tunnel Client Settings", "port"))
    return_dict["username"] = Config.get("Tunnel Client Settings", "username")
    return_dict["password"] = Config.get("Tunnel Client Settings", "password")

    return_dict["ssh_key_location"] = Config.get("SSH Task Settings", "key_location")
    return_dict["ssh_server_addr"] = Config.get("SSH Task Settings", "server_addr")
    return_dict["ssh_server_username"] = Config.get("SSH Task Settings", "server_username")
    return_dict["ssh_server_local_port"] = Config.get("SSH Task Settings", "ssh_local_port")
    return_dict["ssh_server_remote_port"] = Config.get("SSH Task Settings", "ssh_remote_port")

    return return_dict




if __name__ == '__main__':

    settings = readConfig()

    client = Client(settings["server_port"], settings["server_addr"] , settings["username"], settings["password"])

    client_controller = ClientController(client)
    client_controller.tasks["SSH"] = ReverseSSHTask("main_server_reverse_ssh",
                                                    "offline",
                                                    settings["ssh_key_location"],
                                                    settings["ssh_server_addr"],
                                                    settings["ssh_server_username"],
                                                    settings["ssh_server_local_port"],
                                                    settings["ssh_server_remote_port"])
    client_controller.run()