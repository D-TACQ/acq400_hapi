#!/usr/bin/env python

"""
usage: acq400_soft_trigger.py [-h] uut [uut ...]

configure fire a soft trigger

positional arguments:
  uut         uut

optional arguments:
  -h, --help  show this help message and exit
"""

import acq400_hapi
import os
import argparse

parser = argparse.ArgumentParser(description='configure acq400_arm')
parser.add_argument('uut', nargs='+', help="uut")

args = parser.parse_args()
uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]


for u in uuts:
    u.s0.soft_trigger = 1

