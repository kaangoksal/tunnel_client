import json


class ActionHandler(object):
    def __init__(self):
        self.action_handlers = {}
        print("Started")

    def handle_message(self, message):

        """
            action_type: SSH
            command: ssh start
            parameters: name ,remote_port = 7001, local_port =22, key_location = not changable, ssh_server_addr= not changable, username= not changable,

        """
        try:
            payload = json.loads(message.payload)
            action_type = payload["action_type"]

            specific_action_handler = self.action_handlers[action_type]

            return specific_action_handler.handle_message()

        except Exception as e:
            print("Error occured while handling the message, Action Handler " + str(e))
            return False

