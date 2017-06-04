#!/usr/bin/sh
python3 -m swfc_lt_stream.decode localhost | mplayer -demuxer h264es -
