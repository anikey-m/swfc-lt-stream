from swfc_lt_stream import cli, encode


if __name__ == '__main__':
    parser = cli.encoder_parser()
    conf = parser.parse_args()
    encoder = encode.Encoder(conf)
    encoder.run()
