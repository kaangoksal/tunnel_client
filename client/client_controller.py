
import threading
import time
import signal
import sys
from Message import Message
from queue import Queue


class ClientController(object):
    def __init__(self, comm_handler, message_handler):
        """
        Constructore of Client controller
        :param comm_handler: the module that has functions for communications
        :param message_handler: the module that will handle messages
        """
        self.inbox_queue = Queue()
        self.outbox_queue = Queue()

        self.communication_handler = comm_handler
        self.message_handler = message_handler

        self.tasks = {}
        self.running_processes = {}

        self.status = True
        self.receive_thread = None
        self.send_thread = None
        self.logic_thread = None

    def run(self):
        """
        Starts the client controller, also registers termination signal handlers.
        :return: nothing....
        """
        # self.communication_handler.register_signal_handler()
        self.register_signal_handler()
        self.communication_handler.socket_create()
        # When self.status becomes False all the threads quit, this is for terminating the program. ter
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
        """
        This method is for termination of the process ctrl+c, it makes sure that everything goes down nicely.
        :return: nothing
        """
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        """
        This method quits gracefully...
        :param signal: ???
        :param frame: ???
        :return: nothing
        """
        self.status = False
        self.communication_handler.quit_gracefully()
        sys.exit(0)

    def inbox_work(self):
        """
        This method is for receiving messages, it puts the messages into the inbox queue
        :return:
        """
        # TODO optimize blocking
        while self.status:

            received_message = self.communication_handler.read_message()

            if received_message is not None and received_message != b'':
                json_string = received_message.decode("utf-8")
                try:
                    new_message = Message.json_string_to_message(json_string)

                    self.inbox_queue.put(new_message)

                except Exception as e:
                    print("Received bad message " + str(e) + " message was " + str(received_message))
            elif not self.communication_handler.is_server_alive() and self.status:

                print("fuck mate the server is dead! " + str(received_message))
                self.communication_handler.reconnect()

    def outbox_work(self):
        """
        This method is for sending messages, it is launched by a thread, it sends the messages to the server
        from the outbox_queue
        :return:
        """
        # TODO optimize blocking
        # TODO Implement logger
        while self.status:
            print("Outbox Work Queue" + str(self.outbox_queue))
            if self.outbox_queue.not_empty:

                message = self.outbox_queue.get()
                print("Message ready for departure " + str(message))
                self.communication_handler.send_message(message.pack_to_json_string())

            else:
                time.sleep(0.1)
            # print("Finished reading and sending")

    def main_logic(self):
        """
        This method handles the main logic/state machine where the client responds accordingly to appropriate commands.
        :return:
        """
        while self.status:
            if self.inbox_queue.not_empty:
                message_block = self.inbox_queue.get()

                self.message_handler.handle_message(message_block)

    def initialize_threads(self):
        """
        This function initializes the threads that makes the server work
        :return:
        """

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
