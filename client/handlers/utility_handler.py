import time


class UtilityHandler(object):

    def __init__(self, server=None):
        print("Utility Handler Initializing")
        self.server = server

    def initialize(self, server):
        self.server = server
        if self.server is not None:
            self.logger = self.server.logger
        else:
            print("ERROR! UtilityHandler is not initialized properly!")

    def handle_message(self, message):
        """
        This function handles action messages, it finds the appropriate action handler and routes the messages to that handler
        :param message: the message itself
        :return:
        """
        payload = message.payload
        utility_group = payload["utility_group"]

        if utility_group == "ping":
            # print("Updating ping time!")
            old_ping_time = self.server.last_ping
            self.server.last_ping = int(round(time.time()))
            self.logger.debug("[UTILITY handle_message ] updating ping time from " + str(old_ping_time) + " to " + str(self.server.last_ping))
        else:
            # print("Unknown Utility command! " + str(message))
            self.logger.error("[UTILITY handle_message ] unknown utility message "+ str(message))
