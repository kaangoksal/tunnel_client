"""
This module is for handling the messages!
Author: Kaan Goksal
Copyright: It is OPEN SOURCE NOW!
Date: 22 July 2017

"""

# TODO add appropriate threading!
# TODO finish comments and docs


class MessageHandler(object):
    def __init__(self, server=None):
        # self.action_handler = None
        # self.utility_handler = None
        self.handlers = {}
        self.server = server
        self.logger = None

    def initialize(self, server):
        """
        This method initializes the handlers of the Message handler! You can create a message handler object and then
        set its data, server, logger and stuff, after that you should initialize it!
        :param server:
        :return:
        """
        self.server = server
        if self.server is not None:
            self.logger = self.server.logger

            # initializing all the handlers!
            for key in list(self.handlers.keys()):
                handler = self.handlers[key]
                handler.initialize(self.server)

            # self.action_handler.initialize(self.server)
            # self.utility_handler.initialize(self.server)
        else:
            print("ERROR! MessageHandler is not initialized properly!")

    def register_handler(self, handler, type):
        """
        This is for registering message handlers! I did not decide whether this can be called after initialize...
        :param handler:
        :param type:
        :return:
        """
        if type is not None or handler is not None:
            self.handlers[type] = handler

    def handle_message(self, message):
        """
        This method is called when a message is routed to the message handler, this method finds the appropriate message
        handler for the message by looking to its type! It tries to find the message handler and passes the message
        to that!
        :param message: The message that was received.
        :return:
        """
        # This is bad practise...
        specific_handler = self.handlers[str(message.type)]
        if specific_handler is not None:
            specific_handler.handle_message(message)
        else:
            self.logger.error("[Message Handler] cannot find handler for " + str(message))

    def __str__(self):
        handler_string = ""
        for key in list(self.handlers.keys()):
            handler_object = self.handlers[key]
            handler_string += str(handler_object) + " "

        return "MessageHandler Object with handlers: " + handler_string

