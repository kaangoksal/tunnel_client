import datetime
import signal
import sys
import threading

from client.utility.color_print import ColorPrint


class ClientUI(object):
    def __init__(self):
        self.client_controller = None
        self.user_interface_thread = None

    def start(self):
        self.user_interface_thread = threading.Thread(target=self.ui)
        self.user_interface_thread.setName("UI Thread")
        self.user_interface_thread.start()

    def register_signal_handler(self):
        """
        This method registers signal handlers which will do certain stuff before the server terminates
        :return:
        """
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print("Shutting down")
        sys.exit(0)

    def ui(self):
        while self.client_controller.status:
            try:
                print("Please input command [info, tools]")
                user_input = input()
                if user_input == "info":
                    self.ui_info()
                elif user_input == "tools":
                    self.ui_tools()

            except EOFError as e:
                ColorPrint.print_message("Error", "UI", "Exception occurred " + str(e))
        print("UI Terminating")

    def ui_tools(self):
        print("[Tools Panel]")
        print("--------------Options------------")
        print("\n")
        print("1) Disconnect from server (not implemented)")


    def ui_info(self):
        print("[Information Panel]")
        print("-------Running threads----------")
        print("\n")
        for thread in threading.enumerate():
            print(thread)
        print("\n")
        print("-------Connection Statistics----------")
        print("\n")
        print("Total Tunnel Time ", str(datetime.datetime.now() - self.client_controller.connection_date))
        print("Total Reconnetions ", str(self.client_controller.re_connections))
        print("\n")
