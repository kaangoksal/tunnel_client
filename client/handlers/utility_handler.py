import json
from Message import Message
import time


class UtilityHandler(object):

    def __init__(self, server=None):
        self.server = server

    def handle_message(self, message):
        """
        This function handles action messages, it finds the appropriate action handler and routes the messages to that handler
        :param message: the message itself
        :return:
        """
        payload = message.payload
        utility_group = payload["utility_group"]

        if utility_group == "ping":
            print("Updating ping time!")
            self.server.last_ping = int(round(time.time()))

        else:
            print("Unknown Utility command! " + str(message))
