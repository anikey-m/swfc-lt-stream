import enum
import functools
import operator


class Packet(enum.IntEnum):
    connect = 0
    disconnect = 1
    data = 2
    ack = 3


def clean_packet(packet):
    t = packet[0]
    pack_crc = [-1]
    payload = packet[1:-1]
    crc = functools.reduce(operator.xor, payload, t)
    if crc != pack_crc:
        raise ValueError('Invalid packet check sum.')
    return t, payload
