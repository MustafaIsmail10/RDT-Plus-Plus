import threading
import socket


BUFFER_SIZE = 4096
WINDOW_SIZE = 5
MAX_SEQUENCE_NUMBER = 65535
INITIAL_TIMER_INTERVAL = 0.5


class RDT:
    def __init__(
        self,
        sock: socket.socket,
        is_server=True,
        address=None,
    ):
        self.sock = sock
        self.address = address
        self.is_server = is_server

        self.timer_interval = INITIAL_TIMER_INTERVAL
        self.buffer_size = BUFFER_SIZE
        self.window_size = WINDOW_SIZE
        self.max_sequence_number = MAX_SEQUENCE_NUMBER

        self.id = 0

        self.is_connected = False
        self.close_flag = False
        self.is_close_sent = False
        self.exit_flag = False
        self.close_id = None
        self.sending_ended = False
        self.send_buffer = []
        self.waiting_for_ack_buffer = {}
        self.recv_buffer = []
        self.timers = {}

        self.mutex = threading.Lock()
        self.init_condition = threading.Condition(self.mutex)
        self.close_condition = threading.Condition(self.mutex)
        self.sending_condition = threading.Condition(self.mutex)
        self.recv_condition = threading.Condition(self.mutex)

        self.sending_thread = threading.Thread(target=self.sending_thread_func)
        self.receiving_thread = threading.Thread(target=self.receiving_thread_func)

        self.sending_thread.start()
        self.receiving_thread.start()

    def initialize_connection(self):
        """
        This function is called by the client to initialize the connection
        with the server. It sends an initial message to the server and waits
        for an ack. If the ack is not received within a certain time, the
        message is resent.
        """
        with self.mutex:
            msg = f"type:i\nid:{self.id}\nlength:0\n\n"

            self._send(msg, self.address)

            self.waiting_for_ack_buffer[self.id] = msg
            timer = threading.Timer(self.timer_interval, self.resend, [0])
            timer.start()
            self.timers[self.id] = timer
            self.id += 1

            self.init_condition.wait()
            status = self.is_connected
            if not status:
                print(f"Connection failed with {self.address}")
                return False
            else:
                print(f"Connection initialized with {self.address}")
                return True

    def sending_thread_func(self):
        with self.mutex:
            while True:
                if len(self.waiting_for_ack_buffer.keys()) <= self.window_size:
                    if len(self.send_buffer) == 0 and not self.close_flag:
                        self.sending_condition.wait()
                        continue

                    elif len(self.send_buffer) == 0 and self.close_flag:
                        self.close_condition.notify()
                        if self.is_server:
                            self.sending_ended = True
                            self.sending_condition.wait()
                            continue
                        else:
                            print("Sending Thread is dead")
                            return

                    # Locks are acquired
                    message = self.send_buffer.pop(0)
                    id = self.id
                    length = len(message)
                    segment = f"type:d\nid:{id}\nlength:{length}\n\n{message}"
                    self.waiting_for_ack_buffer[id] = segment

                    # Start timer for this sequence number
                    timer = threading.Timer(self.timer_interval, self.resend, [id])
                    timer.start()
                    self.timers[id] = timer

                    # Increment the sequence number
                    self.id += 1
                    if self.id > self.max_sequence_number:
                        self.id = 0
                    self._send(segment, self.address)

                else:
                    self.sending_condition.wait()

    def resend(self, id):
        print(f"Resending segment {id}")
        with self.mutex:
            segment = self.waiting_for_ack_buffer[id]
            self._send(segment, self.address)
            self.timers.pop(id, None)
            timer = threading.Timer(self.timer_interval, self.resend, [id])
            timer.start()
            self.timers[id] = timer

    def ack_handler(self, id):
        self.waiting_for_ack_buffer.pop(id, None)
        timer = self.timers.pop(id, None)
        if timer:
            timer.cancel()

    def receiving_thread_func(self):
        while True:
            message, client_address = self.sock.recvfrom(self.buffer_size)
            message = message.decode("utf-8")
            type, id, length, data = self.message_parser(message)

            if type == "i" and self.is_server:
                with self.mutex:
                    self.is_connected = True
                    self.close_flag = False
                    self.is_close_sent = False
                    self.sending_ended = False
                    self.address = client_address
                    self.id = 0
                    ack = f"type:s\nid:{id}\nlength:0\n\n"
                    self._send(ack, client_address)
                    print(f"Connected from {self.address}")

            elif type == "s" and not self.is_server:
                with self.mutex:
                    self.is_connected = True
                    self.init_condition.notify()
                    timer = self.timers.pop(id, None)
                    if timer:
                        timer.cancel()

            elif type == "a":
                with self.mutex:
                    self.ack_handler(id)
                    self.sending_condition.notify()
                    print(f"Received ack {id}")

                    if (
                        not self.is_server
                        and self.close_flag
                        and self.is_close_sent
                        and len(self.timers.keys()) == 0
                    ):
                        self.close_condition.notify()
                        return
                    elif (
                        self.is_server
                        and self.close_flag
                        and self.sending_ended
                        and len(self.timers.keys()) == 0
                    ):
                        ack = f"type:a\nseq:{self.close_id}\nlength:0\n\n"
                        self._send(ack, self.address)

            elif type == "d":
                with self.mutex:
                    self.recv_buffer.append((data, client_address))
                    print(f"Received segment {id}")
                    self.recv_condition.notify()
                    ack = f"type:a\nid:{id}\nlength:0\n\n"
                    self._send(ack, self.address)
                    print(f"Sent ack {id}")

            elif type == "c":
                with self.mutex:
                    if self.is_server:
                        self.close_flag = True
                        self.close_id = id
                        self.sending_condition.notify()

                    if (
                        self.is_server
                        and self.close_flag
                        and self.sending_ended
                        and len(self.timers.keys()) == 0
                    ):
                        ack = f"type:a\nseq:{self.close_id}\nlength:0\n\n"
                        self._send(ack, self.address)

    def _close_connection_server(self, id):
        with self.mutex:
            self.close_flag = True
            self.sending_condition.notify()
            self.close_condition.wait()

            ack = f"type:a\nseq:{id}\nlength:0\n\n"
            self._send(ack, self.address)

    def close(self):
        with self.mutex:
            self.close_flag = True
            self.sending_condition.notify()

            self.close_condition.wait()
            print("Closing is awake atfter sending is dead")
            id = self.id
            msg = f"type:c\nid:{id}\nlength:0\n\n"

            self.waiting_for_ack_buffer[id] = msg
            timer = threading.Timer(self.timer_interval, self.resend, [id])
            timer.start()
            self.timers[id] = timer

            self.id += 1
            if self.id > self.max_sequence_number:
                self.id = 0

            self._send(msg, self.address)

            self.is_close_sent = True

            self.close_condition.wait()

            print("Reciever  is dead.")

    def _send(self, msg, address):
        """
        Sends a message to the specified address. This function is called
        internally by the class.

        It sends data using udp sockets.
        """
        self.sock.sendto(msg.encode("utf-8"), address)

    def send(self, msg, address):
        """
        This function is called by the upper layer to send data to the network.
        """
        with self.mutex:
            if not self.close_flag:
                self.address = address
                self.send_buffer.append(msg)
                self.sending_condition.notify()
                return True
            else:
                return False

    def recv(self):
        """
        This function is called by the upper layer to receive data from the
        network. It blocks until data is received.
        """
        with self.mutex:
            while len(self.recv_buffer) == 0:
                print("waiting for requests")
                self.recv_condition.wait()
                print("received requests")
            message, address = self.recv_buffer.pop(0)
            return message, address

    def message_parser(self, message):
        """
        This function parses the message received from the network and returns
        the type, sequence number, length and data.
        """
        parts = message.split("\n\n")
        header = parts[0]
        header_parts = header.split("\n")
        type = header_parts[0].split(":")[1]
        id = int(header_parts[1].split(":")[1])
        length = int(header_parts[2].split(":")[1])
        data = parts[1]
        return type, id, length, data
