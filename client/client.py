import getpass
import json
import os
import signal
import socket
import struct
import sys
import time
from Message import Message

# TODO Implement logger


class CommunicationHandler(object):

    def __init__(self, port, host, username, password, software_version="V 0.0.1"):
        self.serverHost = host
        self.serverPort = port
        self.socket = None
        self.username = username
        self.password = password
        self.software_version = software_version

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print('\nQuitting gracefully')
        if self.socket:
            try:
                self.socket.shutdown(2)
                self.socket.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        sys.exit(0)

    def socket_create(self):
        """ Create a socket """
        try:
            self.socket = socket.socket()
        except socket.error as e:
            print("Socket creation error" + str(e))
            return
        return

    def socket_connect(self):
        """ Connect to a remote socket """
        try:
            self.socket.connect((self.serverHost, self.serverPort))
        except socket.error as e:
            print("Socket connection error: " + str(e))
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
            return False

    def reconnect(self):
        self.socket.close()
        self.socket_create()
        connected = False
        while not connected:
            try:
                connected = self.socket_connect()
            except ConnectionRefusedError as e:
                print("Connection refused, trying again in 5 seconds " + str(e))
            time.sleep(5)

    def print_output(self, output_str):
        """ Prints command output """
        sent_message = str.encode(output_str + str(os.getcwd()) + '> ')
        self.socket.send(struct.pack('>I', len(sent_message)) + sent_message)
        print(output_str)
        return

    def send_message(self, output_str):
        """ Sends message to the server
         :param output_str: string message that will go to the server
        """
        print("will send this " + str(output_str))
        byte_array_message = str.encode(output_str)
        # We are packing the lenght of the packet to unsigned big endian
        #  struct to make sure that it is always constant length
        self.socket.send(struct.pack('>I', len(byte_array_message)) + byte_array_message)

        return

    def is_server_alive(self):
        server_conn = self.socket
        try:
            ping_message = Message(self.username, "server", "utility", "ping")
            server_conn.send(str.encode(ping_message.pack_to_json_string()))

        except Exception as e:
            print("Socket probably dead eh? " + str(e))
            return False
        return True

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

    @staticmethod
    def _recvall(conn, n):
        """ Helper function to recv n bytes or return None if EOF is hit
        :param n: length of the packet
        :param conn: socket to read from
        """
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
