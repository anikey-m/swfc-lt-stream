import argparse
from . import sampler


def common_args(parser):
    sampler_group = parser.add_argument_group('Sampler params')
    sampler_group.add_argument(
        '--seed', type=int, default=2067261,
        help='The initial seed for pseudo random number generator.'
    )
    sampler_group.add_argument(
        '-c', type=float, default=sampler.DEFAULT_C,
        help='Degree sampling distribution tuning parameter.'
    )
    sampler_group.add_argument(
        '--delta', type=float, default=sampler.DEFAULT_DELTA,
        help='Degree sampling distribution tuning parameter.'
    )

    codec_group = parser.add_argument_group('Coder params')
    codec_group.add_argument(
        '--chunksize', type=int, default=100,
        help='Size of encoded block in bytes'
    )
    codec_group.add_argument(
        '--window', type=int, default=20,
        help='Size of window (in chunks)'
    )
    codec_group.add_argument(
        '--window-shift', type=int, default=10,
        help='Window shift step (in chunks)'
    )

    parser.add_argument(
        '-p', '--port', type=int, default=6200,
        help='UDP port for data transmitting.'
    )
    parser.add_argument(
        'cmd'
    )
    return parser


def encoder_parser():
    parser = argparse.ArgumentParser(
        description='Encoder/stream server'
    )
    return common_args(parser)


def decoder_parser():
    parser = argparse.ArgumentParser(
        description='Decoder/stream client'
    )
    return common_args(parser)