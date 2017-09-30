import getpass
import json
import os
import signal
import socket
import struct
import sys
import time
import threading
from Message import Message
import logging
import traceback


class CommunicationHandler(object):

    def __init__(self, port, host, username, password, software_version="V 0.0.12"):
        self.serverHost = host
        self.serverPort = port
        self.socket = None
        self.lock = threading.Lock()
        self.connected = False

        self.username = username
        self.password = password
        self.software_version = software_version

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler('client.log')
        console_out = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.addHandler(console_out)
        self.logger.info("client started")

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print('\nQuitting gracefully')
        self.logger.info("Quitting gracefully")
        if self.socket:
            try:
                self.socket.shutdown(2)
                self.socket.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                self.logger.error('Could not close connection %s' % str(e))
                # continue
        sys.exit(0)

    def socket_create(self):
        """ Create a socket """
        try:
            self.socket = socket.socket()
        except socket.error as e:
            print("Socket creation error" + str(e))
            self.logger.error('Socket creation error' + str(e))
            return
        return

    def socket_connect(self):
        """ Connect to a remote socket """
        #with self.lock:
        try:
            self.socket.connect((self.serverHost, self.serverPort))
        except socket.error as e:
            print("Socket connection error: " + str(e))
            self.logger.error('Socket connection error' + str(e))
            time.sleep(5)
            raise
        try:

            return_dict = {
                    'username': self.username,
                    'password': self.password,
                    'hostname': socket.gethostname(),
                    'host_system_username': str(getpass.getuser()),
                    'software_version': self.software_version
               }

            return_string = json.dumps(return_dict, sort_keys=True, indent=4, separators=(',', ': '))
            # print(return_string)

            self.send_message(return_string)
            # TODO look for auth confirmation
            return True

        except socket.error as e:
            print("Cannot send hostname to server: " + str(e))
            self.logger.error("Cannot send auth info to server " + str(e))
            return False

    def reconnect(self):
        # for some reason if the socket is dead you can't turn it off... lame...
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("[reconnect] " + str(e))
            self.logger.error("[reconnect] " + str(traceback.format_exc()))

        self.socket.close()

        self.socket_create()
        self.connected = False
        while not self.connected:
            try:
                self.connected = self.socket_connect()
            except ConnectionRefusedError as e:
                print("Connection refused, trying again in 5 seconds " + str(e))
                self.logger.error("Connection refused, trying again in 5 seconds " + str(e))
                time.sleep(5)

        print("Reconnect successful ")

    def send_message(self, output_str):
        """ Sends message to the server
         :param output_str: string message that will go to the server
        """
        print("will send this " + str(output_str))
        self.logger.debug("will send this message " + str(output_str))
        byte_array_message = str.encode(output_str)
        # We are packing the lenght of the packet to unsigned big endian
        #  struct to make sure that it is always constant length
        #with self.lock:
        self.socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)
        print("Sent!")


    def read_message(self):
        """ Read message length and unpack it into an integer
        """
        raw_msglen = self._recvall(self.socket, 4)

        if not raw_msglen:
            return None
        # We are unpacking a big endian struct which includes the length of the packet,
        # struct makes sure that the header
        # which includes the length is always 4 bytes in length.
        # '>I' indicates that the struct is a unsigned integer big endian
        # CS2110 game strong
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self._recvall(self.socket, msglen)

    def read_message_from_connection(self, conn):
        """ Read message length and unpack it into an integer
        :param conn: the connection to the client, it is a socket object
        """
        raw_msglen = self._recvall(conn, 4)
        if not raw_msglen:
            return None

        # We are unpacking a big endian struct which includes
        # the length of the packet, struct makes sure that the header
        # which includes the length is always 4 bytes in length. '>I'
        # indicates that the struct is a unsigned integer big endian
        # CS2110 game strong

        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self._recvall(conn, msglen)

    def _recvall(self, conn, n):
        """ Helper function to recv n bytes or return None if EOF is hit
        :param n: length of the packet
        :param conn: socket to read from
        """
        #with self.lock:
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
