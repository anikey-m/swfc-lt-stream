import collections
import time
import socket
import select
import sys

from swfc_lt_stream import net, sampler


class Node(object):
    def __init__(self, samples, block):
        self.samples = samples
        self.block = block


class Decoder(object):
    def __init__(self, conf):
        self.sampler = sampler.PRNG(conf.window, conf.c, conf.delta)

        self.chunk_size = conf.chunksize
        self.window_size = conf.window
        self.shift_size = conf.window_shift
        self.dummy = self.window_size - self.shift_size

        self.window_number = None
        self.window = [bytes(self.chunk_size)
                       for _ in range(self.window_size)]
        self.checks = collections.defaultdict(list)
        self.unknown = set(range(
            self.window_size - self.shift_size,
            self.window_size
        ))

        self._metric = conf.metric
        self._packets = 0
        self._extra = 0
        self._total_packets = 0
        self._total_extra = 0

    def shift(self, window=None):
        if type(window) is int:
            if window < self.window_number:
                return
            if window > 0xffffff00 and self.window_size < 0x000000ff:
                return

        if self._metric:
            self._metric.write('Done window {}. Data packets: {}. Extra packets: {}.',
                               self.window_number, self._packets, self._extra)
        self._total_packets += self._packets
        self._total_extra += self._extra
        self._packets = 0
        self._extra = 0

        self.window_number = (self.window_number + 1) % 0xffffffff

        if not self.dummy:
            clean_data = self.window[:self.shift_size]
        elif self.dummy < self.shift_size:
            clean_data = self.window_size[self.dummy:self.shift_size]
            self.dummy = 0
        else:
            self.dummy -= self.shift_size
            clean_data = []

        self.window = self.window[self.shift_size:]
        self.window.extend([bytes(self.chunk_size)] * self.shift_size)
        self.unknown = set(range(
            self.window_size - self.shift_size,
            self.window_size
        ))

        for chunk in clean_data:
            sys.stdout.buffer.write(chunk)

    def consume(self, window, seed, block):
        if window != self.window_number:
            self._extra += 1
            if self.window_number is None:
                self.window_number = window
            else:
                return window

        self._packets += 1

        self.sampler.set_seed(seed)
        _, samples = self.sampler.get_src_blocks()

        if len(samples) == 1:
            self.add_block(next(iter(samples)), block)
        else:
            array = bytearray(block)
            for sample in samples.copy():
                if sample not in self.unknown:
                    for i in range(self.chunk_size):
                        array[i] ^= self.window[sample][i]
                    samples.remove(sample)

            if len(samples) == 1:
                self.add_block(next(iter(samples)), bytes(array))
            elif len(samples) > 1:
                check = Node(samples, array)
                for sample in samples:
                    self.checks[sample].append(check)
        if self.unknown:
            return False
        else:
            return self.window_number

    def add_block(self, sample, block):
        shoud_eleminate = list(self.eliminate(sample, block))
        while shoud_eleminate:
            sample, block = shoud_eleminate.pop()
            shoud_eleminate.extend(self.eliminate(sample, block))

    def eliminate(self, sample, block):
        if sample not in self.unknown:
            return

        self.unknown.remove(sample)
        self.window[sample] = block

        if sample in self.checks:
            nodes = self.checks.pop(sample)

            for node in nodes:
                node.samples.remove(sample)
                for i in range(self.chunk_size):
                    node.block[i] ^= block[i]

                if len(node.samples) == 1:
                    yield next(iter(node.samples)), bytes(node.block)

    def stop(self):
        if self._metric:
            self._metric.write('Total packets {}. Total extra {}.',
                               self._total_packets, self._total_extra)
            self._metric.close()


class Listener(object):
    def __init__(self, host, port, decoder):
        self.decoder = decoder
        self.packet_size = 4096

        self.sock = socket.socket(type=socket.SOCK_DGRAM)
        self.sock.connect((host, port))

    def listen(self):
        try:
            self._listen()
        except:
            self.sock.send(net.build_packet(net.Packet.disconnect, b''))
            self.decoder.stop()
            raise

    def _listen(self):
        while True:
            _, write, _ = select.select([], [self.sock], [])
            self.sock.send(net.build_packet(net.Packet.connect, b''))
            readable, _, _ = select.select([self.sock], [], [], 5)
            try:
                packet = self.sock.recv(self.packet_size)
            except:
                time.sleep(5)
            else:
                break

        while True:
            type_, payload = net.clean_packet(packet)
            if type_ == net.Packet.end:
                return
            elif type_ == net.Packet.data:
                done = self.decoder.consume(*payload)
                if done:
                    self.decoder.shift(done)
                    shift = net.build_shift_packet(done)
                    self.sock.send(shift)
            readable, _, _ = select.select([self.sock], [], [])
            packet = self.sock.recv(self.packet_size)
