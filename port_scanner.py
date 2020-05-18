# We use socket module for scanning ports
import socket

# Threading module for multiple threads
import threading

# We will use Queue to store the list of ports
# since multiple threads run in parallel, its better to have queue for port lists
from queue import SimpleQueue

# Coloring The output
from colorama import Fore, Style

# Regular Expression for host address matching
import re

PORT_LISTENING_CODE = 0
PORT_LISTENING_SYMB = "✔"
PORT_REACHABLE_SYMB = "✗"
PORT_REACHABLE_CODE = 111
PORT_UNREACHABLE_CODE = -1


class PortScanner():
    """Port Scanner Class"""

    def __init__(self, host_name, port_list, thread_num=15, timeout=10):
        self.port_list = port_list
        self.thread_num = thread_num
        self.timeout = timeout
        self.host_name = host_name

        # Call reset to initialize the variables
        self.__reset()

        # Translate Host name to host ip
        self.__get_host_ip(host_name)

    def __get_host_ip(self, host_name):
        """Check if input Host is valid and translate it to ip address"""
        ip_re = re.compile(
            r'((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

        # If Hostname matches the pattern of IP address, then host is IP
        if re.fullmatch(ip_re, host_name.strip(' ')):
            self.host = host_name

        # If Hostname does not match ip pattern, then do dns lookup to find ip
        else:
            self.host = socket.gethostbyname(host_name)

    def __reset(self):
        # Try to delete Port Queue
        try:
            del(self.port_queue)
        except:
            pass

        # Try to delete Open Ports Queue
        try:
            del(self.open_ports_queue)
        except:
            pass

        # Try to delete Open Ports List
        try:
            del(self.open_ports_list)
        except:
            pass

        # Try to delete Thread List
        try:
            del(self.threads_list)
        except:
            pass

        # Re-initialise the variables
        self.port_queue = SimpleQueue()
        self.open_ports_queue = SimpleQueue()
        self.open_ports_list = []
        self.threads_list = []
        self.printing_line = 0

    def __scan_port(self, port):
        """ Function to scan the ports"""
        # Exceptuon handling for cases if port is not reachable
        try:
            # Create Socket Connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set Timeout
            sock.settimeout(self.timeout)

            # Try connection
            res = sock.connect_ex((self.host, port))

            # Port is reachable and listening
            if res == PORT_LISTENING_CODE:
                sock.close()
                return PORT_LISTENING_CODE

            # Port is reachable but not listening
            elif res == PORT_REACHABLE_CODE:
                sock.close()
                return PORT_REACHABLE_CODE

            # Port is unreachable
            else:
                sock.close()
                return PORT_UNREACHABLE_CODE

        # Port is unreachable
        except:
            sock.close()
            return PORT_UNREACHABLE_CODE

    def __fill_queue(self):
        """Function to fill the queue with list of ports"""
        for port in self.port_list:
            self.port_queue.put(port)

    def __worker(self):
        """This is worker method which will be called by each thread.
        This function take 3 arguments
        1. Host to check port on
        2. Queue which has list of ports
        3. Open Ports list which will be used to store open ports identified in program"""

        # Run loop until queue is empty
        while not self.port_queue.empty():

            # Get port from queue
            port = self.port_queue.get()

            if self.__scan_port(port) == PORT_LISTENING_CODE:
                self.open_ports_queue.put(
                    f"{Fore.GREEN}{port} {PORT_LISTENING_SYMB}{Style.RESET_ALL}")
                self.open_ports_list.append(
                    f"{Fore.GREEN}{port} {PORT_LISTENING_SYMB}{Style.RESET_ALL}")

            elif self.__scan_port(port) == PORT_REACHABLE_CODE:
                self.open_ports_queue.put(
                    f"{Fore.CYAN}{port} {PORT_REACHABLE_SYMB}{Style.RESET_ALL}")
                self.open_ports_list.append(
                    f"{Fore.CYAN}{port} {PORT_REACHABLE_SYMB}{Style.RESET_ALL}")

    def __execute_threads(self):
        """This program take the host name, port list and number of threads as input and run the port scanning"""
        # Call reset to reset all variables which might be set by previous Run
        self.__reset()

        # Fill queue
        self.__fill_queue()

        # Create threads and add to thread list
        for _ in range(self.thread_num):
            # Create new thread
            thread = threading.Thread(target=self.__worker)

            # Add thread tp thread list
            self.threads_list.append(thread)

        # Run all threads in thread list
        for thread in self.threads_list:
            thread.start()

    def get_open_ports(self):
        """ Execute all threads and return list if Ports"""
        # Execute the threads
        self.__execute_threads()

        # Join all threads so as to wait for completion
        for thread in self.threads_list:
            thread.join()

        # Return the Open Ports List
        return self.open_ports_list

    def __print_open_port_queue(self):
        """ Print the available ports in open port queue """
        while not self.open_ports_queue.empty():
            # Logic to put new line after every 5 columns
            if self.printing_line == 10:
                print("")
                self.printing_line = 0

            print(f"{self.open_ports_queue.get()}", flush=True, end="\t\t")
            self.printing_line += 1

    def print_open_ports(self):
        """ Execute all threads and print the list of open ports as and when it is found"""

        # Display Host name where port is being scanned
        if self.host == self.host_name:
            host_disp = self.host
        else:
            host_disp = f"{self.host_name}({self.host})"

        print(f"\nScanning for open ports on {host_disp}...", flush=True)

        # Execute the threads
        self.__execute_threads()

        # Print available open ports in queue before running loop
        # this is kept here to avoid skipping all prints if threads are short lived and complete before this point
        self.__print_open_port_queue()

        # Loop to see any ports in port queue
        alive_threads = [thread.is_alive() for thread in self.threads_list]
        while any(alive_threads):
            self.__print_open_port_queue()

            # Re-calculate alive threads
            alive_threads = [thread.is_alive() for thread in self.threads_list]


if __name__ == "__main__":
    # get commandline arguments for host name
    import sys

    if len(sys.argv) < 2:
        host_name = input("Enter the host to scan: ")
    else:
        # Define host for port scanning
        host_name = sys.argv[1]

    # Define Port list
    port_list = range(1, 1025)  # 1 - 1024 port numbers

    # Create instance of Port Scanner
    ps = PortScanner(host_name, port_list, thread_num=20, timeout=5)
    ps.print_open_ports()
    # print(ps.get_open_ports())
