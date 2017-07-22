"""
This module is still in development
Author: Kaan Goksal
Copyright: Centree Technologies
Date: 22 July 2017

"""

from Message import Message


class MessageHandler(object):
    def __init__(self, action_handler, server=None):
        self.action_handler = action_handler
        self.server = server

    def handle_message(self, message):
        if message.type == "action":
            self.action_handler.handle_message(message)
        else:
            print("Message can't be handled " + str(message))

    def __str__(self):
        return "MessageHandler Object with action handler: "+str(self.action_handler)

