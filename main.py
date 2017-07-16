from Client.client_controller import ClientController
from Client.client import Client
import configparser

def readConfig():
    return_dict = {}
    Config = configparser.ConfigParser()
    Config.read("client_config")
    return_dict["server_addr"] = Config.get("Tunnel Client Settings", "host")
    return_dict["server_port"] = int(Config.get("Tunnel Client Settings", "port"))
    return_dict["username"] = Config.get("Tunnel Client Settings", "username")
    return_dict["password"] = Config.get("Tunnel Client Settings", "password")

    return return_dict




if __name__ == '__main__':

    settings = readConfig()

    client = Client(settings["server_port"], settings["server_addr"] , settings["username"], settings["password"])

    client_controller = ClientController(client)
    client_controller.run()