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
import threading
import time


def abort_action(u):
    def _abort_action():        
        u.s0.TIM_CTRL_LOCK = 0
        u.s0.TRANSIENT_SET_ABORT = '1'        
        time.sleep(2)
        u.s0.streamtonowhered = 'stop'
        u.s0.set_abort = 1

        try:
            u.s1.AWG_MODE_ABO = '1'
            u.s1.AWG_MODE_ABO = '0'
        except:
            pass
    return _abort_action
      
parser = argparse.ArgumentParser(description='configure acq400_abort')
parser.add_argument('uut', nargs='+', help="uut")

args = parser.parse_args()
uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]

for u in uuts:
    thx = [ threading.Thread(target=abort_action(u)) for u in uuts ]
    for t in thx:
        t.start()
    for t in thx:
        t.join()    
