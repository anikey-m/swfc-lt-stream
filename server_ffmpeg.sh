#!/usr/bin/sh
python3 -m swfc_lt_stream.encode "ffmpeg -f v4l2 -i /dev/video0 -f h264 -crf 32 -preset ultrafast -vcodec h264 -"
