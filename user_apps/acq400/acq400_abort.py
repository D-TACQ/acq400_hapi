#!/usr/bin/env python

"""
usage: acq400_abort.py [-h] uut [uut ...]

configure acq400_abort

positional arguments:
  uut         uut

optional arguments:
  -h, --help  show this help message and exit
"""

import acq400_hapi
import os
import argparse

parser = argparse.ArgumentParser(description='configure acq400_abort')
parser.add_argument('uut', nargs='+', help="uut")

args = parser.parse_args()
uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]


for u in uuts:
    u.s0.TIM_CTRL_LOCK = 0
    u.s0.streamtonowhered = 'stop'
    u.s0.set_abort = 1





