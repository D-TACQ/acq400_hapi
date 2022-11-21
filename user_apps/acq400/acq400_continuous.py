#!/usr/bin/env python

"""
usage: acq400_continuous.py [-h] uut [uut ...]

control continuous capture, default is to toggle, or use --run=1, --stop=1

positional arguments:
  uut         uut

optional arguments:
  --run=1 
  --stop=1
  -h, --help  show this help message and exit
"""

import acq400_hapi
import argparse

parser = argparse.ArgumentParser(description='configure acq400_arm')
parser.add_argument('-r', '--run',  type=int, help="run continuous")
parser.add_argument('-s', '--stop', type=int, help="stop continuous")
parser.add_argument('uut', nargs='+', help="uut")

args = parser.parse_args()
uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]


for uut in uuts:
    if args.run:
        uut.s0.CONTINUOUS = 'start'
    elif args.stop:
        uut.s0.CONTINUOUS = 'stop'
    else:
        if uut.s0.CONTINUOUS == 'CONTINUOUS start':
            uut.s0.CONTINUOUS = 'stop'
        else:
            uut.s0.CONTINUOUS = 'start'

