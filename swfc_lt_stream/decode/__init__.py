import socket
import select

from swfc_lt_stream import net


class Listener(object):
    def __init__(self, host, port, decoder):
        self.decoder = decoder
        self.packet_size = 1024

        self.sock = socket.socket(type=socket.SOCK_DGRAM)
        self.sock.connect((host, port))

    def listen(self):
        while True:
            _, write, _ = select.select([], [self.sock], [])
            self.sock.send(net.build_packet(net.Packet.connect, b''))
            readable, _, _ = select.select([self.sock], [], [], 5)
            if readable:
                break

        while True:
            readable, _, _ = select.select([self.sock], [], [])
            packet = self.sock.recv(self.packet_size)
            type_, payload = net.clean_packet(packet)
            if type_ == net.Packet.end:
                return
            elif type_ == net.Packet.data:
                done = self.decoder.consume(payload)
                if done:
                    shift = net.build_shift_packet(done)
                    self.sock.send(shift)
