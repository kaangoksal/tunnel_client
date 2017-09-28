
import threading
import time
import signal
import logging
import select
import sys
from Message import Message
from queue import Queue
import datetime


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
        self.ping_thread = None

        self.ping_time = 5
        self.ping_deadline = 60
        self.last_ping = int(round(time.time()))

        self.server_alive_check = 0
        self.server_connection_error_threshold = 5

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
        while self.status:
                while self.communication_handler.connected:
                    readable, writable, exceptional = select.select([self.communication_handler.socket], [], [])
                    #print("Block resumed!")
                    for connection in readable:

                        try:
                            received_message = self.communication_handler.read_message_from_connection(connection)
                        except Exception as e:
                            self.logger.error("[inbox_work] Exception occured while reading socket " + str(e))
                            received_message = None

                        if received_message is not None and received_message != b'':
                            print("[inbox_work] received message " + received_message.decode("utf-8"))
                            json_string = received_message.decode("utf-8")
                            try:
                                new_message = Message.json_string_to_message(json_string)

                                self.inbox_queue.put(new_message)

                            except Exception as e:
                                print("[inbox_work] Received bad message " + str(e) + " message was " + str(received_message))
                                self.logger.error("[inbox_work] Received bad message " + str(e) + " message was " + str(received_message))
                        elif not self.is_server_alive() and self.status:

                            print("[inbox_work] fuck mate the server is dead! " + str(received_message))
                            self.logger.error("[inbox_work] The server appears to be dead " + str(received_message))
                            #self.communication_handler.reconnect()
                    #print("end of a loop")
                time.sleep(5)

    def outbox_work(self):
        """
        This method is for sending messages, it is launched by a thread,
        it sends the messages to the server, it terminates if the connections breaks
        from the outbox_queue
        :return:
        """
        while self.status:
            time.sleep(5) # waiting for reconnectione!
            while self.communication_handler.connected:
                # while not self.communication_handler.connected:
                #     self.logger.error("Waiting for reconnection to the server, outbox work")
                #     time.sleep(1)

                message = self.outbox_queue.get(block=True)
                print("[outbox_work] Message ready for departure " + str(message))
                self.logger.debug("[outbox_work] Message ready for departure " + str(message))
                try:
                    self.communication_handler.send_message(message.pack_to_json_string())
                except Exception as e:
                    self.logger.error("[outbox_work] Exception occurred during send " + str(e))
                    if not self.is_server_alive() and self.status:
                        self.outbox_queue.put(message) # put back the message because it was not sent!
                        print("[outbox_work] fuck mate the server is dead! Couldn't send the message " + str(message))
                        self.logger.error("[outbox_work] The server appears to be dead Couldn't send the message "
                                          + str(message))

    def ping_work(self):
        while self.status:
            time.sleep(1)
            while self.communication_handler.connected:
                seconds_now = int(round(time.time()))
                if seconds_now - self.last_ping < self.ping_deadline:

                    time.sleep(self.ping_time)

                    ping_payload = {"utility_group": "ping"}

                    ping_message = Message(self.communication_handler.username, "server", "utility", ping_payload)

                    self.outbox_queue.put(ping_message)
                else:

                    # self.communication_handler.connected = False # We don't need this actually
                    print("Disconnected! ")
                    self.logger.warning("[ping work] ping reply expired, setting connected to false")
                    self.communication_handler.connected = False

    def is_server_alive(self):
        self.server_alive_check += 1
        if self.server_alive_check < self.server_connection_error_threshold:
            return True
        else:
            self.logger.warning("[is_server_alive] error threshold passed, triggering disconnect")
            self.communication_handler.connected = False
            return False

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

        self.ping_thread = threading.Thread(target=self.ping_work)
        self.ping_thread.setName("Ping Thread")
        self.ping_thread.start()

        # Experimental, this loop checks whether the threads are alive, if not, it restarts them.
        while self.status:
            if not self.communication_handler.connected:
                self.logger.error("[Main Thread] Lost connection, will start trying to reconnect")
                try:
                    self.communication_handler.reconnect()
                    self.logger.info("[Main Thread] Connection resumed, resuming operations")
                    self.server_alive_check = 0
                    self.last_ping = int(round(time.time()))
                except Exception as e:
                    self.logger.error("[Main Thread] error reconnecting: " +str(e))

            if not self.receive_thread.is_alive() and self.communication_handler.connected:
                self.logger.error("[Main Thread] receive thread is dead will restart")
                try:
                    self.receive_thread = threading.Thread(target=self.inbox_work)
                    self.receive_thread.setName("Receive Thread")
                    self.receive_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Error restarting receive thread " + str(e))

            if not self.send_thread.is_alive() and self.communication_handler.connected:
                self.logger.error("[Main Thread] send thread is dead will restart")
                try:
                    self.send_thread = threading.Thread(target=self.outbox_work)
                    self.send_thread.setName("Send Thread")
                    self.send_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Error restarting send thread "+ str(e))

            if not self.logic_thread.is_alive():
                self.logger.error("[Main Thread] message_router thread is dead will restart")
                try:
                    self.logic_thread = threading.Thread(target=self.main_logic)
                    self.logic_thread.setName("Message Router Thread")
                    self.logic_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] error restarting logic thread " + str(e))

            if not self.ping_thread.is_alive() and self.communication_handler.connected:
                self.logger.error("[Main Thread] ping thread is dead will restart")
                try:
                    self.ping_thread = threading.Thread(target=self.ping_work)
                    self.ping_thread.setName("Ping Thread")
                    self.ping_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Error restarting ping thread " + str(e))

        time.sleep(1)
