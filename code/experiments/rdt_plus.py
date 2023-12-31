"""
This module implements RDT+ protocol. It is using RDT protocol as a base.
RDT+ protocol is used to send multiple objects over the network.

It receives a list of objects, split them into segments, interleave them and send them over the network.

It also receives segments, reorder them and construct the original object.
"""

from rdt import RDT
import ast

MAX_SEGMENT_SIZE = 2048


class RDTPlus:
    """
    This class implements RDT+ protocol. It is using RDT protocol as a base.
    RDT+ protocol is used to send multiple objects over the network.

    It implements invervalve and reordering of segments.
    """

    def __init__(self, sock, is_server=True, server_address_port=None):
        """
        This method initializes RDT+ protocol.
        It receives a socket, is_server flag and server_address_port.
        If is_server is True, server_address_port should be None.
        If is_server is False, server_address_port should be the address of the server.

        It initializes the send_obj_id, recv_objects and recv_objects_ids attributes.
        The send_obj_id is used to identify the objects that are sent or received.
        The recv_objects is a dictionary that contains the objects that are received.
        The recv_objects_ids is a list of the ids of the objects that are received.
        The completed_objects_ids is a list of the ids of the objects that are completed.
        """
        self.rdt = RDT(sock, is_server, server_address_port)
        if not is_server:
            if server_address_port is None:
                raise ValueError("server_address_port cannot be None")
            self.rdt.initialize_connection()
        self.send_obj_id = 0
        self.recv_objects = {}
        self.recv_objects_ids = []
        self.completed_objects_ids = []

    def send(self, msgs: list, address_port):
        """
        This method sends a list of objects over the network.
        It receives a list of objects and the address of the receiver.
        It splits the objects into segments, interleave them and send them over the network.
        """
        send_objects_dic = {}
        for msg in msgs:
            if msg is None:
                continue
            elif len(msg) > MAX_SEGMENT_SIZE:
                segments = self._split_msg(msg)
                segments_num = len(segments)
            else:
                segments = [msg]
                segments_num = 1

            send_objects_dic[self.send_obj_id] = [segments, segments_num, 0]
            self.send_obj_id += 1

        messages = self._construct_messages(send_objects_dic)
        self.rdt.send_many(messages, address_port)

    def _split_msg(self, msg):
        """
        This method splits a message into segments.
        It receives a message and split it into segments.
        It returns a list of segments.
        """
        segments = []
        while msg:
            segments.append(msg[:MAX_SEGMENT_SIZE])
            msg = msg[MAX_SEGMENT_SIZE:]
        return segments

    def _construct_messages(self, objects_dic):
        """
        This method constructs messages from segmented objects.
        It receives a dictionary of objects.
        It returns a list of messages that are constructed from interleved segments of objects.
        """
        messages = []
        is_still_remaning_segments_to_send = True
        while is_still_remaning_segments_to_send:
            is_still_remaning_segments_to_send = False
            for obj_id, obj in objects_dic.items():
                segments, segments_num, segments_sent = obj
                if segments_sent < segments_num:
                    is_still_remaning_segments_to_send = True
                    msg_to_send = (
                        f"obj_id:{obj_id}\nsegments_num:{segments_num}\nsegment_id:{segments_sent}\n\n"
                        + str(segments[segments_sent])
                    )

                    msg_to_send = msg_to_send.encode("utf-8")
                    messages.append(msg_to_send)
                    objects_dic[obj_id] = (
                        segments,
                        segments_num,
                        segments_sent + 1,
                    )

        return messages

    def _parse_msg(self, msg):
        """
        This method parses a message.
        """
        msg = msg.split("\n\n")
        header = msg[0].split("\n")
        body = msg[1]
        obj_id = int(header[0].split(":")[1])
        segments_num = int(header[1].split(":")[1])
        segment_id = int(header[2].split(":")[1])

        return obj_id, segments_num, segment_id, body

    def _construct_object(self, obj_id):
        """
        This method constructs an object from segments.
        It receives an object id and construct the object from segments.
        It returns the object.
        """
        segments, segments_num, address, segments_recv = self.recv_objects[obj_id]
        object = ""
        ## order segments
        segments.sort(key=lambda x: x[0])
        for segment in segments:
            object += segment[1]

        return object

    def recv(self):
        """
        This method receives a list of objects over the network.

        It stores the objects in recv_objects dictionary.

        If an object is completed, it constructs the object and return it along with the sender address.
        """
        while True:
            msg, address = self.rdt.recv()
            msg = msg.decode("utf-8")
            obj_id, segments_num, segment_id, body = self._parse_msg(msg)

            if obj_id in self.completed_objects_ids:
                continue
            elif obj_id in self.recv_objects_ids:
                if segment_id in [x[0] for x in self.recv_objects[obj_id][0]]:
                    continue
                self.recv_objects[obj_id][0].append((segment_id, body))
                self.recv_objects[obj_id][3] += 1

            else:
                self.recv_objects_ids.append(obj_id)
                self.recv_objects[obj_id] = [
                    [(segment_id, body)],
                    segments_num,
                    address,
                    1,
                ]

            if self.recv_objects[obj_id][3] == segments_num:
                self.completed_objects_ids.append(obj_id)
                self.recv_objects_ids.remove(obj_id)
                object = self._construct_object(obj_id)
                self.recv_objects.pop(obj_id)
                object = ast.literal_eval(object)
                return object, address

    def close(self):
        """
        This method closes the connection.
        """
        self.rdt.close()

    def cleanup_server(self):
        """
        This method cleans up the server. It should be called after the server is closed.
        """
        self.send_obj_id = 0
        self.recv_objects = {}
        self.recv_objects_ids = []
        self.completed_objects_ids = []
