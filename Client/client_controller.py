
import threading
import time
from Message import Message
from Client.client import received_queue
from Client.client import will_send_queue
from Client.tasks.reverse_ssh_task import ReverseSSHTask


class ClientController(object):
    def __init__(self, comm_handler):
        self.communication_handler = comm_handler
        self.tasks = {}
        self.running_processes = {}

    def run(self):
        self.communication_handler.register_signal_handler()
        self.communication_handler.socket_create()
        while True:
            try:
                self.communication_handler.socket_connect()
            except Exception as e:
                print("Error on socket connections: %s" % str(e))
                time.sleep(5)
            else:
                break
        try:
            self.initialize_threads()
        except Exception as e:
            print('Error in main: ' + str(e))
        # print("Amigos I go")

    def inbox_work(self):
        # TODO optimize blocking
        while 1:

            received_message = self.communication_handler.read_message()

            if received_message is not None and received_message != b'':
                json_string = received_message.decode("utf-8")
                try:
                    new_message = Message.json_string_to_message(json_string)

                    received_queue.put(new_message)

                except Exception as e:
                    print("Received bad message " + str(e) + " message was " + str(received_message))
            elif not self.communication_handler.is_server_alive():

                print("fuck mate the server is dead! " + str(received_message))
                self.communication_handler.reconnect()

    def outbox_work(self):
        # TODO optimize blocking
        # TODO Implement logger
        if will_send_queue.not_empty:

            message = will_send_queue.get()
            print("Message ready for departure " + str(message))
            self.communication_handler.send_message(message.pack_to_json_string())

        else:
            time.sleep(0.1)
        # print("Finished reading and sending")

    def main_logic(self):
        while 1:
            if received_queue.not_empty:
                message_block = received_queue.get()

                # sender, type_of_message, message = message_block

                # print("Main Logic Reporting! Sender " + str(sender) +
                #  " type_of_message " + type_of_message + " message " + message)
                if message_block.type == "action":
                    # TODO incorporate username, system username, hostname to message
                    if message_block.payload == "SSH-Start":
                        print("Firing the ssh tunnel!")

                        reverse_ssh_job = self.tasks["SSH"]
                        reverse_ssh_job.status = "started"

                        reverse_ssh_job.start_connection()
                        self.running_processes["SSH"] = reverse_ssh_job
                        result_message = Message(self.communication_handler.username, "server", "result", "SSH Started")

                        will_send_queue.put(result_message)

                    elif message_block.payload == "SSH-Stop":
                        print("Stopping the ssh tunnel!")
                        # TODO incorporate hostname, system username to message
                        reverse_ssh_job = self.running_processes["SSH"]

                        print("Reverse SSH Task PID status " + str(reverse_ssh_job.stop_connection()))

                        self.running_processes.pop('key', None)

                        result_message = Message(self.communication_handler.username, "server", "result", "SSH Stopped")

                        will_send_queue.put(result_message)
                else:
                    print("Message received! " + str(message_block))

    def initialize_threads(self):

        # This thread receives messages from the server
        receive_thread = threading.Thread(target=self.inbox_work)
        receive_thread.setName("Receive Thread")
        receive_thread.start()

        # This thread sends messages to the server
        send_thread = threading.Thread(target=self.outbox_work)
        send_thread.setName("Send Thread")
        send_thread.start()

        # This thread listens to the received messages and does stuff according to them
        logic_thread = threading.Thread(target=self.main_logic)
        logic_thread.setName("Logic Thread")
        logic_thread.start()
