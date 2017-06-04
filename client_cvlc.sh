#!/usr/bin/sh
python3 -m swfc_lt_stream.decode 192.168.0.1 | cvlc - :demux=h264
