# -*- coding: utf-8 - *-
import struct
import SocketServer
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from StringIO import StringIO
import threading
import uuid
import MySQLdb
import time


class WebSocketsHandler(SocketServer.StreamRequestHandler):
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    user_id = ''
    opponent_id = ''
    operation = 1
    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        print "connection established", self.client_address
        self.handshake_done = False

    def handle(self):
        while True:
            if not self.handshake_done:
                self.handshake()
            else:
                self.read_next_message()

    def read_next_message(self):
        length = ord(self.rfile.read(2)[1]) & 127
        if length == 126:
            length = struct.unpack(">H", self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.rfile.read(8))[0]
        masks = [ord(byte) for byte in self.rfile.read(4)]
        decoded = ""
        for char in self.rfile.read(length):
            decoded += chr(ord(char) ^ masks[len(decoded) % 4])
        self.on_message(decoded)

    def send_message(self, message):
        print self.user_id
        print message
        self.request.send(chr(129))
        length = len(message)
        if length <= 125:
            self.request.send(chr(length))
        elif 126 <= length <= 65535:
            self.request.send(126)
            self.request.send(struct.pack(">H", length))
        else:
            self.request.send(127)
            self.request.send(struct.pack(">Q", length))
        self.request.send(message)

    def handshake(self):
        data = self.request.recv(1024).strip()
        headers = Message(StringIO(data.split('\r\n', 1)[1]))
        if headers.get("Upgrade", None) != "websocket":
            return
        print 'Handshaking...'
        key = headers['Sec-WebSocket-Key']
        digest = b64encode(sha1(key + self.magic).hexdigest().decode('hex'))
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: %s\r\n\r\n' % digest
        self.handshake_done = self.request.send(response)

    def get_opponent(self, top):
        """
        matched the opponent
        :return:the opponent id
        """
        global end, matched, max_num, max_time, id, next_link, pre_link, opponent_matched, opponent_id, timestamp
        while int(time.time())-timestamp[end] > max_time:
            end = next_link[end]
        while matched[end] == 1:
            end = next_link[end]
        if con.acquire():
            if top != end:
                matched[end] = 1
                opponent_id[top] = id[end]
                pre_link[next_link[top]] = pre_link[top]
                next_link[pre_link[top]] = next_link[top]
                opponent_matched[end] = 1
                opponent_id[end] = id[top]
                opponent = id[end]
                end = next_link[end]
                con.notify()
                con.release()
                time.sleep(1)
                return opponent
            elif matched[top] == 0:
                con.wait()
                if matched[top] == 1:
                    con.release()
                    time.sleep(1)
                    return opponent_id[top]
                else:
                    con.wait()

            elif matched[top] == 1:
                con.release()
                time.sleep(1)
                return opponent_id[top]

    def on_message(self, message):
        """
        deal with the massage
        :param message: the message that client send
        :return:
        """
        global top, max_num, next_link, id, matched, pre_link
        num = message[0]
        t = top - 1 + max_num
        t = t % max_num
        print t
        if num == '2':
            self.user_id = str(uuid.uuid1())
            top = (top + 1)
            top = top % max_num 
            next_link[top] = next_link[t]
            pre_link[top] = t 
            next_link[t] = top
            id[top] = self.user_id
            matched[top] = 0
            opponent_matched[top] = 0
            timestamp[top] = int(time.time())
            self.opponent_id = self.get_opponent(top)
        else:
            pass
con = threading.Condition()
# conn = MySQLdb.connect(
#     host='localhost',
#     port=3306,
#     user='root',
#     passwd='Eden@mysql',
#     db='memeda',
#     unix_socket='/tmp/mysql.sock',
# )
# cur = conn.cursor()

top = 0
end = 0
max_num = 50000
max_time = 1000
id = range(max_num)
matched = (range(max_num))
next_link = (range(max_num))
pre_link = (range(max_num))
opponent_matched = range(max_num)
timestamp = range(max_num)
opponent_id = range(max_num)
energy_list = [-1, -2, -4, -8, 0, -1, 0, 0, 1]
result_list = [[2, 1, 1, 1, 2, 2, 0, 2, 0],
               [0, 2, 1, 1, 2, 2, 0, 2, 0],
               [0, 0, 2, 1, 0, 2, 0, 2, 0],
               [0, 0, 0, 2, 0, 2, 0, 2, 0],
               [2, 2, 1, 1, 2, 2, 2, 2, 2],
               [2, 2, 2, 2, 2, 2, 2, 2, 2],
               [1, 1, 1, 1, 2, 2, 2, 0, 2],
               [2, 2, 2, 2, 2, 2, 1, 2, 2],
               [1, 1, 1, 1, 2, 2, 2, 2, 2]]
if __name__ == "__main__":
    server = SocketServer.ThreadingTCPServer(
        ("120.24.64.232", 8888), WebSocketsHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "GOT ^C!,Bye"
        server.server_close()
