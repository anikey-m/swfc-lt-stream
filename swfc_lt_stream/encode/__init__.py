import select
import socket
import subprocess

from swfc_lt_stream import net, sampler


class Encoder(object):
    def __init__(self, conf):
        self.conf = conf
        self._reader = None
        self.packet_size = 1024

        self.sampler = sampler.PRNG(conf.window, conf.c, conf.delta)
        self.sampler.set_seed(conf.seed)

        self.window_size = conf.window * conf.chunksize
        self.window_shift = conf.window_shift * conf.chunksize
        self.window = bytearray(self.window_size)
        self.window_number = 0

        self.sock = socket.socket(type=socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', conf.port))
        self.sock.setblocking(0)

        self.remain = 0  # self.window_shift

        self._stream = False

    def run(self):
        while True:
            select.select([self.sock], [], [])
            packet, client = self.sock.recvfrom(self.packet_size)
            try:
                t, payload = net.clean_packet(packet)
                assert t == net.Packet.connect
            except:
                continue
            self.sock.connect(client)
            self.stream()

    def stream(self):
        self._stream = True
        self._reader = subprocess.Popen(
            self.conf.cmd, shell=True, stdout=subprocess.PIPE
        )
        try:
            while self._stream:
                self.loop()
            self._reader.wait(timeout=1)
        finally:
            if self._reader.returncode is None:
                self._reader.kill()

    def loop(self):
        read, write, _ = select.select([self.sock], [self.sock], [])

        if read:
            self.read_packet()
        if write:
            self.write_packet()

    def read_packet(self):
        try:
            t, payload = net.clean_packet(self.sock.read(self.packet_size))
        except:
            return

        if t == net.Packet.disconnect:
            self._stream = False
        elif t == net.Packet.ack:
            pass

    def write_packet(self):
        a = self._reader.stdout.read(10)
        print(a)
        if a:
            self.sock.send(a)
