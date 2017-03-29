from swfc_lt_stream import cli, encode


if __name__ == '__main__':
    parser = cli.encoder_parser()
    conf = parser.parse_args()

    source = encode.Source(conf.cmd)
    encoder = encode.Encoder(source, conf)
    server = encode.Streamer(encoder, conf.port)
    server.run()
