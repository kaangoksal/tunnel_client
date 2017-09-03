
import threading
import time
import signal
import logging
import select
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

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler('client.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.info("client started")

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
                self.logger.error("Error on socket connections:  %s" % str(e))
                print("Error on socket connections: %s" % str(e))
                time.sleep(5)
            else:  # This breaks when the connection succeeds
                break
        try:
            self.communication_handler.connected = True
            self.initialize_threads()
        except Exception as e:
            print('Could not initialize threads: ' + str(e))
            self.logger.error("Could not initialize threads " + str(e))
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

    # def inbox_work(self):
    #     """
    #     This method is for receiving messages, it puts the messages into the inbox queue
    #     :return:
    #     """
    #     while self.status:
    #
    #         while not self.communication_handler.connected:
    #             self.logger.error("Waiting for reconnection to the server, inbox work")
    #             time.sleep(1)
    #         # Blocking call
    #         received_message = self.communication_handler.read_message()
    #
    #         if received_message is not None and received_message != b'':
    #             print("received message " + received_message.decode("utf-8"))
    #             json_string = received_message.decode("utf-8")
    #             try:
    #                 new_message = Message.json_string_to_message(json_string)
    #
    #                 self.inbox_queue.put(new_message)
    #
    #             except Exception as e:
    #                 print("Received bad message " + str(e) + " message was " + str(received_message))
    #                 self.logger.error("Received bad message " + str(e) + " message was " + str(received_message))
    #         elif not self.communication_handler.is_server_alive() and self.status:
    #
    #             print("fuck mate the server is dead! " + str(received_message))
    #             self.logger.error("The server appears to be dead " + str(received_message))
    #             self.communication_handler.reconnect()

    def inbox_work(self):
        while self.status:
            readable, writable, exceptional = select.select([self.communication_handler.socket], [], [])
            print("Block resumed!")
            for connection in readable:
                received_message = self.communication_handler.read_message_from_connection(connection)

                if received_message is not None and received_message != b'':
                    print("received message " + received_message.decode("utf-8"))
                    json_string = received_message.decode("utf-8")
                    try:
                        new_message = Message.json_string_to_message(json_string)

                        self.inbox_queue.put(new_message)

                    except Exception as e:
                        print("Received bad message " + str(e) + " message was " + str(received_message))
                        self.logger.error("Received bad message " + str(e) + " message was " + str(received_message))
                elif not self.communication_handler.is_server_alive() and self.status:

                    print("fuck mate the server is dead! " + str(received_message))
                    self.logger.error("The server appears to be dead " + str(received_message))
                    self.communication_handler.reconnect()
            print("end of a loop")



    def outbox_work(self):
        """
        This method is for sending messages, it is launched by a thread, it sends the messages to the server
        from the outbox_queue
        :return:
        """
        while self.status:
            while not self.communication_handler.connected:
                self.logger.error("Waiting for reconnection to the server, outbox work")
                time.sleep(1)

            message = self.outbox_queue.get(block=True)
            print("Message ready for departure " + str(message))
            self.logger.debug("Message ready for departure " + str(message))
            self.communication_handler.send_message(message.pack_to_json_string())

    def main_logic(self):
        """
        This method handles the main logic/state machine where the client responds accordingly to appropriate commands.
        :return:
        """
        while self.status:
            # Blocking call
            message_block = self.inbox_queue.get(block=True)
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

        # Experimental, this loop checks whether the threads are alive, if not, it restarts them.
        while self.status:
            try:
                if not self.receive_thread.is_alive():
                    self.logger.error("[Main Thread] receive thread is dead")
                    receive_thread = threading.Thread(target=self.inbox_work)
                    receive_thread.setName("Receive Thread")
                    receive_thread.start()

                if not self.send_thread.is_alive():
                    self.logger.error("[Main Thread] send thread is dead")
                    send_thread = threading.Thread(target=self.outbox_work)
                    send_thread.setName("Send Thread")
                    send_thread.start()

                if not self.logic_thread.is_alive():
                    self.logger.error("[Main Thread] message_router thread is dead")
                    message_router_thread = threading.Thread(target=self.main_logic)
                    message_router_thread.setName("Message Router Thread")
                    message_router_thread.start()
            except Exception as e:
                self.logger.error("Error restarting a new thread! ")
                time.sleep(5)
            time.sleep(1)
