import json
from Message import Message


class UtilityHandler(object):

    def __init__(self, server=None):
        self.server = server

    def handle_message(self, message):
        """
        This function handles action messages, it finds the appropriate action handler and routes the messages to that handler
        :param message: the message itself
        :return:
        """
        #try:
        payload = json.loads(message.payload)
        utility_type = payload["utility_type"]

        if utility_type == "PING":
            print("Replying to ping")
            ping_reply_message = Message(self.server.communication_handler.username, "server", "utility", "ping reply")
            self.server.outbox_queue.put(ping_reply_message)
        else:
            print("Unknown Utility command! " + str(message))
