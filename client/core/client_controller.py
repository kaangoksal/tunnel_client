import datetime
import logging
import select
import signal
import sys
import threading
import time
import traceback
from queue import Queue

from client.models.Message import Message


class ClientController(object):
    def __init__(self, socket_layer, message_handler):
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
        console_out = logging.StreamHandler(sys.stdout)
        #self.logger.addHandler(console_out)
        self.logger.info("client started")

        self.inbox_queue = Queue()
        self.outbox_queue = Queue()

        self.socket_layer = socket_layer
        self.message_handler = message_handler

        self.message_handler.initialize(self)

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

        self.re_connections = 0
        self.connection_date = datetime.datetime.now()
    def run(self):
        """
        Starts the client controller, also registers termination signal handlers.
        :return: nothing....
        """
        # self.socket_layer.register_signal_handler()
        self.register_signal_handler()
        self.socket_layer.socket_create()
        # When self.status becomes False all the threads quit, this is for terminating the program. ter
        self.status = True
        while True:
            try:
                self.socket_layer.socket_connect()
            except Exception as e:
                self.logger.error("Error on socket connections:  %s" % str(e))
                # print("Error on socket connections: %s" % str(e))
                time.sleep(5)
            else:  # This breaks when the connection succeeds
                break
        try:
            self.socket_layer.connected = True
            self.initialize_threads()
        except Exception as e:
            # print('Could not initialize threads: ' + str(e))
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
        self.socket_layer.quit_gracefully()
        sys.exit(0)

    def inbox_work(self):
        while self.status:
                while self.socket_layer.connected:
                    readable, writable, exceptional = select.select([self.socket_layer.socket], [], [])
                    # print("Block resumed!")
                    for connection in readable:

                        try:
                            received_message = self.socket_layer.read_message_from_connection(connection)
                        except Exception as e:
                            self.logger.error("[inbox_work] Exception occured while reading socket " + str(e))
                            received_message = None

                        if received_message is not None and received_message != b'':
                            # print("[inbox_work] received message " + received_message.decode("utf-8"))
                            self.logger.debug("[inbox_work] received message " +  str(received_message.decode("utf-8")) )
                            json_string = received_message.decode("utf-8")
                            try:
                                new_message = Message.json_string_to_message(json_string)

                                self.inbox_queue.put(new_message)

                            except Exception as e:
                                # print("[inbox_work] Received bad message " + str(e) + " message was " + str(received_message))
                                self.logger.error("[inbox_work] Received bad message " + str(e) + " message was " + str(received_message))
                        elif not self.is_server_alive() and self.status:

                            # print("[inbox_work] fuck mate the server is dead! " + str(received_message))
                            self.logger.error("[inbox_work] The server appears to be dead " + str(received_message))
                            #self.socket_layer.reconnect()
                    ## print("end of a loop")
                time.sleep(5)

    def outbox_work(self):
        """
        This method is for sending messages, it is launched by a thread,
        it sends the messages to the server, it terminates if the connections breaks
        from the outbox_queue
        :return:
        """
        while self.status:
            while self.socket_layer.connected:
                # while not self.socket_layer.connected:
                #     self.logger.error("Waiting for reconnection to the server, outbox work")
                #     time.sleep(1)

                message = self.outbox_queue.get(block=True)
                try:
                    self.socket_layer.send_message(message.pack_to_json_string())
                    self.logger.debug("[outbox_work] Message sent " + str(message))
                except Exception as e:
                    self.logger.error("[outbox_work] Exception occurred during send " + str(e))
                    if not self.is_server_alive() and self.status:
                        self.outbox_queue.put(message) # put back the message because it was not sent!
                        # print("[outbox_work] fuck mate the server is dead! Couldn't send the message " + str(message))
                        self.logger.error("[outbox_work] The server appears to be dead Couldn't send the message "
                                          + str(message))
            time.sleep(5)  # waiting for reconnectione!

    def ping_work(self):
        while self.status:
            while self.socket_layer.connected:
                seconds_now = int(round(time.time()))
                if seconds_now - self.last_ping < self.ping_deadline:

                    time.sleep(self.ping_time) # we don't want to have a fucking cpu spin

                    ping_payload = {"utility_group": "ping"}

                    ping_message = Message(self.socket_layer.username, "server", "utility", ping_payload)

                    self.outbox_queue.put(ping_message)
                else:

                    # self.socket_layer.connected = False # We don't need this actually
                    # print("[ping work] ping reply expired, setting connected to false " + str(seconds_now - self.last_ping))
                    # print("Self last ping ", self.last_ping)
                    # print("Now ", seconds_now)

                    self.logger.warning("[ping work] ping reply expired, setting connected to false " + str(seconds_now - self.last_ping))
                    self.logger.warning("Self last ping " + str(self.last_ping))
                    self.logger.warning("Now " + str(seconds_now))

                    self.socket_layer.connected = False

    def is_server_alive(self):
        self.server_alive_check += 1
        if self.server_alive_check < self.server_connection_error_threshold:
            return True
        else:
            # print("[is_server_alive] error threshold passed, triggering disconnect")
            self.logger.warning("[is_server_alive] error threshold passed, triggering disconnect")
            self.socket_layer.connected = False
            return False

    def main_logic(self):
        """
        This method handles the main logic/state machine where the client responds accordingly to appropriate commands.
        :return:
        """
        while self.status:
            # Blocking call so no cpu spin, chill brah
            message_block = self.inbox_queue.get(block=True)
            self.logger.debug("[main logic] handling a message! " + str(message_block))
            self.message_handler.handle_message(message_block)

    def initialize_threads(self):
        """
        This function initializes the threads that makes the server work
        :return:
        """
        # TODO create higher level threads! ones that can be restarted

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

        from client.logic.console_ui import ClientUI

        shit_ui = ClientUI()
        shit_ui.client_controller = self
        shit_ui.start()


        # Experimental, this loop checks whether the threads are alive, if not, it restarts them.
        while self.status:
            time.sleep(1) # this prohibits fackin cpu spin
            if not self.socket_layer.connected:
                self.logger.error("[Main Thread] Lost connection, will start trying to reconnect")
                try:
                    self.socket_layer.reconnect()
                    self.logger.info("[Main Thread] Connection resumed, resuming operations")
                    self.server_alive_check = 0
                    self.last_ping = int(round(time.time()))
                    self.re_connections += 1
                    self.connection_date = datetime.datetime.now()

                except Exception as e:
                    self.logger.error("[Main Thread] error reconnecting: " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))
                    time.sleep(10)

            if not self.receive_thread.is_alive() and self.socket_layer.connected:
                self.logger.error("[Main Thread] receive thread is dead will restart")
                try:
                    self.receive_thread = threading.Thread(target=self.inbox_work)
                    self.receive_thread.setName("Receive Thread")
                    self.receive_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Error restarting receive thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            if not self.send_thread.is_alive() and self.socket_layer.connected:
                self.logger.error("[Main Thread] send thread is dead will restart")
                try:
                    self.send_thread = threading.Thread(target=self.outbox_work)
                    self.send_thread.setName("Send Thread")
                    self.send_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Error restarting send thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            if not self.logic_thread.is_alive():
                self.logger.error("[Main Thread] message_router thread is dead will restart")
                try:
                    self.logic_thread = threading.Thread(target=self.main_logic)
                    self.logic_thread.setName("Message Router Thread")
                    self.logic_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] error restarting logic thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))

            if not self.ping_thread.is_alive() and self.socket_layer.connected:
                self.logger.error("[Main Thread] ping thread is dead will restart")
                try:
                    self.ping_thread = threading.Thread(target=self.ping_work)
                    self.ping_thread.setName("Ping Thread")
                    self.ping_thread.start()
                except Exception as e:
                    self.logger.error("[Main Thread] Error restarting ping thread " + str(e))
                    self.logger.error("[Main Thread] " + str(traceback.format_exc()))


