import os
import select
import socket
import subprocess

from swfc_lt_stream import net, sampler


class NoDataException(Exception):
    pass


class Source(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            self.cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(tiemeout=1)
            except:
                self.proc.kill()
            self.proc = None

    def read(self, size):
        if self.proc is None:
            raise NoDataException()
        remain = size
        buffer = b''
        while remain:
            readable, _, _ = select.select([self.proc.stdout.fileno()], [], [])
            part = os.read(readable[0], remain)
            if part:
                remain -= len(part)
                buffer += part
            else:
                if remain:
                    buffer += bytes(remain)
                if self.proc.poll() is not None:
                    self.proc = None
                break
        return buffer

    def end(self):
        return self.proc is None


class Encoder(object):
    def __init__(self, source, conf):
        self.source = source

        self.sampler = sampler.PRNG(conf.window, conf.c, conf.delta)
        self.sampler.set_seed(conf.seed)

        self.chunk_size = conf.chunksize
        self.window_size = conf.window
        self.shift_size = conf.window_shift

        self.window_number = 0
        self.window = [bytearray(self.chunk_size)
                       for _ in range(self.window_size)]

    def shift(self, window_num=None):
        if window_num is None or window_num == self.window_number:
            if self.source.end():
                raise NoDataException()
            window = self.window[self.shift_size:]
            for _ in range(self.shift_size):
                try:
                    window.append(bytearray(self.source.read(self.chunk_size)))
                except NoDataException:
                    window.append(bytearray(self.chunk_size))
            self.window = window
            self.window_number = (self.window_number + 1) % 0xffffffff

    def build_packet(self):
        blockseed, samples = self.sampler.get_src_blocks()
        block = bytearray(self.chunk_size)
        for sample in samples:
            for i in range(self.chunk_size):
                block[i] ^= self.window[sample][i]
        return self.window_number, blockseed, block

    def __enter__(self):
        self.source.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.source.stop()


class Streamer(object):
    def __init__(self, encoder, port):
        self.encoder = encoder
        self.packet_size = 1024

        self.sock = socket.socket(type=socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.setblocking(0)

        self._stream = False
        self._sl = [self.sock]
        self._empty = []

        self.client = None

    def run(self):
        while True:
            select.select(self._sl, self._empty, self._empty)
            packet, self.client = self.sock.recvfrom(self.packet_size)
            try:
                t, payload = net.clean_packet(packet)
                assert t == net.Packet.connect
            except:
                continue
            self.stream()
            self.client = None

    def stream(self):
        with self.encoder:
            self._stream = True
            self.encoder.shift()
            while self._stream:
                read, write, _ = select.select(self._sl, self._sl, self._empty)
                if read:
                    self.read_packet()
                if write:
                    self.write_packet()

    def read_packet(self):
        try:
            t, payload = net.clean_packet(self.sock.recv(self.packet_size))
        except:
            return

        if t == net.Packet.disconnect:
            self._stream = False
        elif t == net.Packet.ack:
            window_num, = payload
            try:
                self.encoder.shift(window_num)
            except NoDataException:
                self._stream = False

    def write_packet(self):
        if not self._stream:
            packet = net.build_packet(net.Packet.end, b'')
            self.sock.sendto(packet, self.client)
            return

        window, blockseed, block = self.encoder.build_packet()
        packet = net.build_data_packet(window, blockseed, block)
        try:
            self.sock.sendto(packet, self.client)
        except:
            pass
