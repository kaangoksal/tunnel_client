"""
This module is still in development
Author: Kaan Goksal
Copyright: Centree Technologies
Date: 22 July 2017

"""

from Message import Message
from Message import MessageType

class MessageHandler(object):
    def __init__(self, server=None):
        self.action_handler = None
        self.utility_handler = None
        self.server = server

    def initialize(self, server):
        self.server = server
        if self.server is not None:
            self.logger = self.server.logger

            self.action_handler.initialize(self.server)
            self.utility_handler.initialize(self.server)
        else:
            print("ERROR! MessageHandler is not initialized properly!")

    def handle_message(self, message):
        if message.type == MessageType.action:
            self.action_handler.handle_message(message)
        elif message.type == MessageType.utility:
            self.utility_handler.handle_message(message)
        else:
            # print("Message can't be handled " + str(message))
            self.logger.error("[MessageHandler] message can't be handled! " + str(message))

    def __str__(self):
        return "MessageHandler Object with action handler: " + str(self.action_handler)

