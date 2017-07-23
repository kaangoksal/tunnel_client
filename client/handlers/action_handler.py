import json


class ActionHandler(object):

    def __init__(self, server=None):
        self.server = server
        self.action_handlers = {}

    def handle_message(self, message):
        """
        This function handles action messages, it finds the appropriate action handler and routes the messages to that handler
        :param message: the message itself
        :return:
        """
        #try:
        payload = json.loads(message.payload)
        action_type = payload["action_type"]

        specific_action_handler = self.action_handlers[action_type]

        return specific_action_handler.handle_message(message)

        #except Exception as e:
            #print("Error occured while handling the message, Action Handler " + str(e))
            #return False

