#!/usr/bin/env python

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





