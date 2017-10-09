import json


class ActionHandler(object):
    def __init__(self, server=None):
        self.server = server
        self.logger = None
        self.handlers = {}

    def initialize(self, server):
        self.server = server
        if self.server is not None:
            self.logger = self.server.logger

            for key in list(self.handlers.keys()):
                handler = self.handlers[key]
                handler.initialize(self.server)
        else:
            print("ERROR! ActionHandler is not initialized properly!")

    def register_handler(self, handler, handler_type):
        """
        This is for registering message handlers! I did not decide whether this can be called after initialize...
        :param handler:
        :param handler_type:
        :return:
        """
        if handler_type is not None or handler is not None:
            self.handlers[handler_type] = handler

    def handle_message(self, message):
        """
        This function handles action messages, it finds the appropriate action handler and routes the messages to that handler
        :param message: the message itself
        :return:
        """
        # try:
        payload = json.loads(message.payload)
        action_type = payload["action_type"]

        specific_action_handler = self.handlers[action_type]

        return specific_action_handler.handle_message(message)

        # except Exception as e:
        # print("Error occured while handling the message, Action Handler " + str(e))
        # return False

