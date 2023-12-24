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
        self.timer_interval = INITIAL_TIMER_INTERVAL
        self.is_server = is_server
        self.buffer_size = BUFFER_SIZE

        self.send_buffer = []
        self.waiting_for_ack_buffer = {}
        self.window_size = WINDOW_SIZE
        self.next_sequence_number = 0
        self.max_sequence_number = MAX_SEQUENCE_NUMBER

        self.timers = {}
        self.timers_lock = threading.Lock()

        self.recv_buffer = []
        self.recv_buffer_lock = threading.Lock()
        self.recv_mutex = threading.Lock()
        self.recv_condition = threading.Condition(self.recv_mutex)

        self.send_buffer_lock = threading.Lock()
        self.waiting_for_ack_buffer_lock = threading.Lock()

        self.sending_mutex = threading.Lock()
        self.sending_condition = threading.Condition(self.sending_mutex)
        self.sending_thread = threading.Thread(target=self.sending_thread_func)

        self.receiving_thread = threading.Thread(target=self.receiving_thread_func)

        self.is_running = True
        self.is_running_lock = threading.Lock()

        self.sending_thread.start()
        self.receiving_thread.start()

        if not self.is_server:
            self.initialize_connection()

    def initialize_connection(self):
        msg = "type:i\nseq:0\nlength:0\n\n"
        self._send(msg)
        self.waiting_for_ack_buffer_lock.acquire()
        self.waiting_for_ack_buffer[0] = msg
        self.next_sequence_number += 1
        self.waiting_for_ack_buffer_lock.release()
        self.timers_lock.acquire()
        timer = threading.Timer(self.timer_interval, self.resend, [0])
        timer.start()
        self.timers[0] = timer
        self.timers_lock.release()
        print("Sent initial message")
        print("Waiting for ack")

    def _send(self, msg):
        self.sock.sendto(msg.encode("utf-8"), self.address)

    def sendto(self, msg, address):
        with self.sending_mutex:
            self.send_buffer_lock.acquire()
            self.address = address
            self.send_buffer.append(msg)
            self.send_buffer_lock.release()
            self.sending_condition.notify()

    def recv(self):
        with self.recv_mutex:
            self.recv_buffer_lock.acquire()
            while len(self.recv_buffer) == 0:
                self.recv_buffer_lock.release()
                print("waiting for message")
                self.recv_condition.wait()
                print("received message")

            with self.is_running_lock:
                if not self.is_running:
                    return None, None

            self.recv_buffer_lock.acquire()
            message, address = self.recv_buffer.pop(0)
            self.recv_buffer_lock.release()
            return message, address

    def sending_thread_func(self):
        with self.sending_mutex:
            while True:
                if len(self.waiting_for_ack_buffer.keys()) <= self.window_size:
                    self.send_buffer_lock.acquire()
                    self.waiting_for_ack_buffer_lock.acquire()
                    if len(self.send_buffer) == 0:
                        self.send_buffer_lock.release()
                        self.waiting_for_ack_buffer_lock.release()
                        self.sending_condition.wait()
                        continue
                    # Locks are acquired
                    message = self.send_buffer.pop(0)
                    seq = self.next_sequence_number
                    length = len(message)
                    segment = f"type:d\nseq:{seq}\nlength:{length}\n\n{message}"
                    self.waiting_for_ack_buffer[seq] = segment

                    # Start timer for this sequence number
                    timer = threading.Timer(self.timer_interval, self.resend, [seq])
                    timer.start()
                    self.timers_lock.acquire()
                    self.timers[seq] = timer
                    self.timers_lock.release()

                    # Increment the sequence number
                    self.next_sequence_number += 1
                    if self.next_sequence_number > self.max_sequence_number:
                        self.next_sequence_number = 0

                    self._send(segment)
                    self.send_buffer_lock.release()
                    self.waiting_for_ack_buffer_lock.release()
                else:
                    self.sending_condition.wait()

                with self.is_running_lock:
                    if not self.is_running:
                        break

    def message_parser(self, message):
        parts = message.split("\n\n")
        header = parts[0]
        header_parts = header.split("\n")
        type = header_parts[0].split(":")[1]
        seq = int(header_parts[1].split(":")[1])
        length = int(header_parts[2].split(":")[1])
        data = parts[1]
        return type, seq, length, data

    def ack_handler(self, seq):
        with self.sending_mutex:
            self.waiting_for_ack_buffer_lock.acquire()
            self.waiting_for_ack_buffer.pop(seq, None)
            self.waiting_for_ack_buffer_lock.release()
            self.sending_condition.notify()

    def receiving_thread_func(self):
        while True:
            message, client_address = self.sock.recvfrom(self.buffer_size)
            message = message.decode("utf-8")
            type, seq, length, data = self.message_parser(message)
            if type == "i" and self.is_server:
                self.address = client_address
                ack = f"type:a\nseq:{seq}\nlength:0\n\n"
                self.next_sequence_number = seq + 1
                self.sock.sendto(ack.encode("utf-8"), client_address)
                print("Received initial message")
                print("Sent ack")

            elif type == "a":
                self.ack_handler(seq)
                self.timers_lock.acquire()
                timer = self.timers.pop(seq, None)
                if timer:
                    timer.cancel()
                self.timers_lock.release()
                print(f"Received ack {seq}")

            elif type == "d":
                self.recv_buffer_lock.acquire()
                self.recv_buffer.append((data, client_address))
                self.recv_buffer_lock.release()
                print(f"Received segment {seq}")
                with self.recv_mutex:
                    self.recv_condition.notify()
                ack = f"type:a\nseq:{seq}\nlength:0\n\n"
                self.sock.sendto(ack.encode("utf-8"), client_address)
                print(f"Sent ack {seq}")
            elif type == "c":
                self.close()
            with self.is_running_lock:
                if not self.is_running:
                    break

    def resend(self, seq):
        print(f"Resending segment {seq}")
        self.waiting_for_ack_buffer_lock.acquire()
        segment = self.waiting_for_ack_buffer[seq]
        self.waiting_for_ack_buffer_lock.release()
        self._send(segment)
        self.timers_lock.acquire()
        self.timers.pop(seq, None)
        timer = threading.Timer(self.timer_interval, self.resend, [seq])
        timer.start()
        self.timers[seq] = timer

    def _clean_timers(self):
        self.timers_lock.acquire()
        for seq, timer in self.timers.items():
            timer.cancel()
        self.timers_lock.release()

    def close(self):
        self.sendto("type:c\nseq:0\nlength:0\n\n", self.address)
        with self.is_running_lock:
            self.is_running = False

        self._clean_timers()

        with self.sending_condition:
            self.sending_condition.notify()

        with self.recv_condition:
            self.recv_condition.notify()

        self.sending_thread.join()
        self.receiving_thread.join()
        self.sock.close()
