#!/usr/bin/env python3
from swfc_lt_stream import cli, decode


if __name__ == '__main__':
    parser = cli.decoder_parser()
    conf = parser.parse_args()

    decoder = decode.Decoder(conf)
    client = decode.Listener(conf.host, conf.port, decoder)
    client.listen()
