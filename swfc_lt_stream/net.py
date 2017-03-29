import enum
import functools
import operator
import struct


class Packet(enum.IntEnum):
    connect = 0
    disconnect = 1
    data = 2
    ack = 3
    end = 4


def build_data_packet(blockseed, block):
    payload = struct.pack('!I', blockseed) + block
    return build_packet(Packet.data, payload)


def build_packet(type_, payload):
    crc = functools.reduce(operator.xor, payload, type_)
    packet = struct.pack('!B%dsB' % len(payload), type_, payload, crc)
    return packet


def clean_packet(packet):
    type_, payload, pack_crc = struct.unpack('!B%dsB' % (len(packet)-2), packet)
    crc = functools.reduce(operator.xor, payload, type_)
    if crc != pack_crc:
        raise ValueError('Invalid packet check sum.')
    return type_, payload
