# We use socket module for scanning ports
import socket

# Threading module for multiple threads
import threading

# We will use Queue to store the list of ports
# since multiple threads run in parallel, its better to have queue for port lists
from queue import Queue


class PortScanner():
    """Port Scanner Class"""

    def __init__(self, host, port_list, thread_num=10):
        self.host = host
        self.port_list = port_list
        self.thread_num = thread_num
        self.port_queue = Queue()
        self.open_ports = []
        
        # Fill queue
        self.fill_queue()

    def scan_port(self, port):
        """ Function to scan the ports"""
        # Exceptuon handling for cases if port is not reachable
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, port))
            sock.close()
            return True
        except:
            return False

    def fill_queue(self):
        """Function to fill the queue with list of ports"""
        for port in self.port_list:
            self.port_queue.put(port)


    def worker(self):
        """This is worker method which will be called by each thread.
        This function take 3 arguments
        1. Host to check port on
        2. Queue which has list of ports
        3. Open Ports list which will be used to store open ports identified in program"""
        
        # Run loop until queue is empty
        while not self.port_queue.empty():

            # Get port from queue
            port = self.port_queue.get()

            if self.scan_port(port):
                self.open_ports.append(port)


    def execute(self):
        """This program take the host name, port list and number of threads as input and run the port scanning"""
        # Create list of threads for waiting till all threads are completed.
        threads_list = []

        # Create threads and add to thread list
        for _ in range(self.thread_num):
            # Create new thread
            thread = threading.Thread(target=self.worker)

            # Add thread tp thread list
            threads_list.append(thread)

        # Run all threads in thread list
        for thread in threads_list:
            thread.start()

        # Join all threads so as to wait for completion
        for thread in threads_list:
             thread.join()
        
        return self.open_ports

if __name__ == "__main__":
    # get commandline arguments for host name
    import sys
    
    if len(sys.argv) < 2:
        print("Provide hpst name from command line")
    else:
        # Define host for port scanning
        host = sys.argv[1] 

        # Define Port list
        port_list = range(1, 1024)

        # Create instance of Port Scanner
        ps = PortScanner(host, port_list, 10)
        print(ps.execute())
