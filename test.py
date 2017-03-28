#!/usr/bin/env python
from . import parser


parser1 = parser.encoder_parser()
print(parser1.parse_args())
