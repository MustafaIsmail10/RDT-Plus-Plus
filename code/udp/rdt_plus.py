from rdt import RDT
import ast

MAX_SEGMENT_SIZE = 2048


class RDTPlus:
    def __init__(self, sock, is_server=True, server_address_port=None):
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
        segments = []
        while msg:
            segments.append(msg[:MAX_SEGMENT_SIZE])
            msg = msg[MAX_SEGMENT_SIZE:]
        return segments

    def _construct_messages(self, objects_dic):
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
        msg = msg.split("\n\n")
        header = msg[0].split("\n")
        body = msg[1]
        obj_id = int(header[0].split(":")[1])
        segments_num = int(header[1].split(":")[1])
        segment_id = int(header[2].split(":")[1])

        return obj_id, segments_num, segment_id, body

    def _construct_object(self, obj_id):
        segments, segments_num, address, segments_recv = self.recv_objects[obj_id]
        object = ""
        ## order segments
        segments.sort(key=lambda x: x[0])
        for segment in segments:
            object += segment[1]

        return object

    def recv(self):
        while True:
            msg, address = self.rdt.recv()
            msg = msg.decode("utf-8")
            obj_id, segments_num, segment_id, body = self._parse_msg(msg)

            if obj_id in self.completed_objects_ids:
                continue
            elif obj_id in self.recv_objects_ids:
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
        self.rdt.close()

    def cleanup_server(self):
        self.send_obj_id = 0
        self.recv_objects = {}
        self.recv_objects_ids = []
        self.completed_objects_ids = []
