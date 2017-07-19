
import threading
import time
import signal
import sys
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
        #self.communication_handler.register_signal_handler()
        self.register_signal_handler()
        self.communication_handler.socket_create()
        self.status = True
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

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal= None, frame= None):
        self.status = False
        self.communication_handler.quit_gracefully()
        sys.exit(0)


    def inbox_work(self):
        # TODO optimize blocking
        while self.status:

            received_message = self.communication_handler.read_message()

            if received_message is not None and received_message != b'':
                json_string = received_message.decode("utf-8")
                try:
                    new_message = Message.json_string_to_message(json_string)

                    received_queue.put(new_message)

                except Exception as e:
                    print("Received bad message " + str(e) + " message was " + str(received_message))
            elif not self.communication_handler.is_server_alive() and self.status:

                print("fuck mate the server is dead! " + str(received_message))
                self.communication_handler.reconnect()

    def outbox_work(self):
        # TODO optimize blocking
        # TODO Implement logger
        while self.status:
            print("Outbox Work Queue" + str(will_send_queue))
            if will_send_queue.not_empty:

                message = will_send_queue.get()
                print("Message ready for departure " + str(message))
                self.communication_handler.send_message(message.pack_to_json_string())

            else:
                time.sleep(0.1)
            # print("Finished reading and sending")

    def main_logic(self):
        while self.status:
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
        self.receive_thread = threading.Thread(target=self.inbox_work)
        self.receive_thread.setName("Receive Thread")
        self.receive_thread.start()

        # This thread sends messages to the server
        self.send_thread = threading.Thread(target=self.outbox_work)
        self.send_thread.setName("Send Thread")
        self.send_thread.start()

        # This thread listens to the received messages and does stuff according to them
        self.logic_thread = threading.Thread(target=self.main_logic)
        self.logic_thread.setName("Logic Thread")
        self.logic_thread.start()
