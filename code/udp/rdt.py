"""
rdt is a reliable data transfer protocol that uses UDP sockets. It is used
by the upper layer to send and receive small segments of data.
"""


import threading
import socket
import ast
import hashlib

BUFFER_SIZE = 4096
WINDOW_SIZE = 1000
MAX_SEQUENCE_NUMBER = 65535
INITIAL_TIMER_INTERVAL = 0.5


class RDT:
    """
    This class implements the RDT protocol. It is used by the upper layer to
    send and receive segments.

    It uses the following attributes:
    sock: The socket used for sending and receiving data.
    is_server: A boolean indicating whether the object is a server or a client.
    address: The address of the other end of the connection.
    timer_interval: The time interval for the timer.
    buffer_size: The size of the buffer used for sending and receiving data.
    window_size: The size of the window used for sending data.
    max_sequence_number: The maximum sequence number.
    id: The sequence number of the next segment to be sent.
    is_connected: A boolean indicating whether the connection is established.
    close_flag: A boolean indicating whether the connection is to be closed.
    is_close_sent: A boolean indicating whether the close message is sent.
    exit_flag: A boolean indicating whether the connection is closed.
    close_id: The sequence number of the close message.
    sending_ended: A boolean indicating whether the sending is ended.
    send_buffer: A list of messages to be sent.
    waiting_for_ack_buffer: A dictionary of messages waiting for ack.
    recv_buffer: A list of received messages.
    timers: A dictionary of timers.
    mutex: A mutex used for synchronization.
    init_condition: A condition variable used for synchronization while initializing the connection.
    close_condition: A condition variable used for synchronization while closing the connection.
    sending_condition: A condition variable used for synchronization while sending data.
    recv_condition: A condition variable used for synchronization while receiving data.
    sending_thread: A thread used for sending data.
    receiving_thread: A thread used for receiving data.
    """

    def __init__(
        self,
        sock: socket.socket,
        is_server=True,
        address=None,
    ):
        """
        This function initializes the RDT object. It takes a socket, a boolean
        indicating whether the object is a server or a client and the address
        of the other end of the connection as input.

        It initializes the attributes of the class.

        It starts the sending and receiving threads.
        """
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
            # Send initial message, start timer and wait for ack.
            checksum = self.compute_checksum("i", self.id, 0, "")
            msg = self.message_formatter("i", self.id, 0, checksum, "")
            self._send(msg, self.address)
            self.waiting_for_ack_buffer[self.id] = msg
            timer = threading.Timer(self.timer_interval, self.resend, [0])
            timer.start()
            self.timers[self.id] = timer
            self.id += 1
            self.init_condition.wait()

            # If the connection is not established, return False.
            # Otherwise, return True.
            status = self.is_connected
            if not status:
                print(f"Connection failed with {self.address}")
                return False
            else:
                print(f"Connection initialized with {self.address}")
                return True

    def compute_checksum(self, type, id, length, message):
        """
        This function computes the checksum of the message. It takes the type,
        sequence number, length and data as input and returns the checksum.
        """
        payload = self.message_formatter(type, id, length, 0, message)
        hash_function = hashlib.md5()
        hash_function.update(payload.encode("utf-8"))
        checksum = hash_function.hexdigest()
        return checksum

    def sending_thread_func(self):
        """
        This function is the target of the sending thread. It sends the data
        in the send buffer to the other end of the connection up to the window size.

        It also handles the close procedure. If the close flag is set and send buffer
        is empty, it notifies the close condition. If the object is a server, it waits
        for the sending thread to end. If the object is a client, it returns.
        """

        with self.mutex:
            while True:
                #  Wait until the window is not full.
                if len(self.waiting_for_ack_buffer.keys()) <= self.window_size:
                    # if the send buffer is empty and the close flag is not set, wait.
                    if len(self.send_buffer) == 0 and not self.close_flag:
                        self.sending_condition.wait()
                        continue

                    # if the send buffer is empty and the close flag is set, notify the close condition.
                    elif len(self.send_buffer) == 0 and self.close_flag:
                        self.close_condition.notify()
                        if self.is_server:
                            self.sending_ended = True
                            self.sending_condition.wait()
                            continue
                        else:
                            return

                    # get the message from the send buffer and send it.
                    message = self.send_buffer.pop(0)
                    id = self.id
                    length = len(message)
                    checksum = self.compute_checksum("d", id, length, message)
                    segment = self.message_formatter("d", id, length, checksum, message)
                    self.waiting_for_ack_buffer[id] = segment

                    # Start timer for this sequence number
                    timer = threading.Timer(self.timer_interval, self.resend, [id])
                    timer.start()
                    self.timers[id] = timer

                    # Increment the sequence number
                    self.id += 1
                    if self.id > self.max_sequence_number:
                        self.id = 0

                    # Send the message
                    self._send(segment, self.address)

                else:
                    self.sending_condition.wait()  # wait until the window is not full

    def resend(self, id):
        """
        This function is called when the timer for a message expires. It resends
        the message and restarts the timer.
        """
        with self.mutex:
            segment = self.waiting_for_ack_buffer[id]
            self.timers.pop(id, None)
            self._send(segment, self.address)
            timer = threading.Timer(self.timer_interval, self.resend, [id])
            timer.start()
            self.timers[id] = timer

    def ack_handler(self, id):
        """
        This function is called when an ack is received. It cancels the timer
        for the message and removes the message from the waiting for ack buffer.
        """
        self.waiting_for_ack_buffer.pop(id, None)
        timer = self.timers.pop(id, None)
        if timer:
            timer.cancel()

    def receiving_thread_func(self):
        """
        This function is the target of the receiving thread. It receives the
        data from the network and handles the received data.

        It listens on the socket and receives data. It parses the received data
        and checks the header. If the header is corrupted, it continues listening.
        If the header is not corrupted, it checks the checksum. If the checksum
        is not equal to the computed checksum, it continues listening. If the
        checksum is equal to the computed checksum, it handles the message.

        If the message is an initial message, it sends an ack and sets the
        connection status to True. If the message is an ack, it handles the ack.

        If the message is a data message, it adds the message to the receive
        buffer and sends an ack.

        If the message is a close message, it sets the close flag to True waits for appropriate
        conditions to close the connection by sending ack to the close message.
        """
        while True:
            message, client_address = self.sock.recvfrom(self.buffer_size)
            message = message.decode("utf-8")
            type, id, length, checksum, data, is_header_corrupted = self.message_parser(
                message
            )
            if is_header_corrupted:  # The header is corrupted. It can not be parsed.
                continue
            computed_checksum = self.compute_checksum(type, id, length, data)
            # The checksum is not equal to the computed checksum.
            # The message is corrupted.
            if computed_checksum != checksum:
                continue
            if type == "i" and self.is_server:
                with self.mutex:
                    self.is_connected = True
                    self.close_flag = False
                    self.is_close_sent = False
                    self.sending_ended = False
                    self.address = client_address
                    self.id = 0
                    checksum = self.compute_checksum("s", id, 0, "")
                    ack = self.message_formatter("s", id, 0, checksum, "")
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
                        checksum = self.compute_checksum("a", self.close_id, 0, "")
                        ack = self.message_formatter(
                            "a", self.close_id, 0, checksum, ""
                        )
                        self._send(ack, self.address)

            elif type == "d":
                with self.mutex:
                    self.recv_buffer.append((data, client_address))
                    self.recv_condition.notify()
                    checksum = self.compute_checksum("a", id, 0, "")
                    ack = self.message_formatter("a", id, 0, checksum, "")
                    self._send(ack, self.address)

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
                        checksum = self.compute_checksum("a", self.close_id, 0, "")
                        ack = self.message_formatter(
                            "a", self.close_id, 0, checksum, ""
                        )
                        self._send(ack, self.address)

    def close(self):
        """
        This function is called by the upper layer in the client to close the connection.

        It sets the close flag to True and notifies the sending condition. It waits
        for the close condition to be notified. It sends a close message and waits
        for an ack. If the ack is not received within a certain time, the message
        is resent.
        """
        with self.mutex:
            self.close_flag = True
            self.sending_condition.notify()

            self.close_condition.wait()
            id = self.id
            checksum = self.compute_checksum("c", id, 0, "")
            msg = self.message_formatter("c", id, 0, checksum, "")
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

    def send_many(self, msgs, address):
        with self.mutex:
            if not self.close_flag:
                self.address = address
                for msg in msgs:
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
                self.recv_condition.wait()
            message, address = self.recv_buffer.pop(0)
            return message, address

    def message_formatter(self, type, id, length, checksum, data):
        """
        This function formats the message to be sent over the network.
        """
        message = (
            f"type:{type}\nid:{id}\nlength:{length}\nchecksum:{checksum}\n\n{data}"
        )
        return message

    def message_parser(self, message):
        """
        This function parses the message received from the network and returns
        the type, sequence number, length and data.
        """
        is_header_corrupted = False
        try:
            parts = message.split("\n\n")
            header = parts[0]
            header_parts = header.split("\n")
            type = header_parts[0].split(":")[1]
            id = int(header_parts[1].split(":")[1])
            length = int(header_parts[2].split(":")[1])
            checksum = header_parts[3].split(":")[1]
            if len(parts) > 1 and len(parts[1]) > 0:
                data = ast.literal_eval(parts[1])
            else:
                data = ""
        except Exception as e:
            is_header_corrupted = True
            type = None
            id = None
            length = None
            checksum = None
            data = None
        return type, id, length, checksum, data, is_header_corrupted
