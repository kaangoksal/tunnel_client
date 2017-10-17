from client.client_controller import ClientController
from client.client_socket import SocketLayer
from client.handlers.message_handler import MessageHandler
from client.handlers.action_handler import ActionHandler
from client.handlers.ssh_action_handler import SshActionHandler
from client.handlers.utility_handler import UtilityHandler


import configparser


def read_config():
    return_dict = {}
    config = configparser.ConfigParser()
    config.read("client_config")
    config_sections = config.sections()

    for config_section in config_sections:
        config_section_options = config.options(config_section)
        config_section_dict = {}
        for config_section_option in config_section_options:
            config_section_dict[config_section_option] = config.get(config_section, config_section_option)
        return_dict[config_section] = config_section_dict

    return return_dict


if __name__ == '__main__':

    settings = read_config()
    # Create the socket layer which will deal with sockets and messages in a lower level

    socket_layer_settings = settings['Tunnel Client Settings']

    socket_layer = SocketLayer(int(socket_layer_settings["port"]),
                               socket_layer_settings["host"],
                               socket_layer_settings["username"],
                               socket_layer_settings["password"])

    # Create action handler
    action_handler = ActionHandler()
    # Create child handlers of the action handler
    ssh_settings = settings['SSH Task Settings']
    ssh_action_handler = SshActionHandler(ssh_settings)

    # register the handlers to the action handler
    action_handler.register_handler(ssh_action_handler, "SSH")

    # create utility handler
    utility_handler = UtilityHandler()

    # Create the main handler
    message_handler = MessageHandler()

    # register the child handlers to the main handler
    message_handler.register_handler(action_handler, "action")
    message_handler.register_handler(utility_handler, "utility")

    # Create a client_controller which will recursively initialize the handlers
    client_controller = ClientController(socket_layer, message_handler)
    # threads fire up and the client is online!
    client_controller.run()
