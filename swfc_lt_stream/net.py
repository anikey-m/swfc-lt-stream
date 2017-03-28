import enum
import functools
import operator


class Packet(enum.IntEnum):
    connect = ord('0')
    disconnect = ord('1')
    data = ord('2')
    ack = ord('3')


def clean_packet(packet):
    t, *payload, pack_crc = packet
    crc = functools.reduce(operator.xor, payload, t)
    if crc != pack_crc:
        pass
        # raise ValueError('Invalid packet check sum.')
    return t, payload
