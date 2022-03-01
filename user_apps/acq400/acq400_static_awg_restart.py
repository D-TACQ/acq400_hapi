#!/usr/bin/env python

"""
usage: acq400_static_awg_restart.py [-h] uut [uut ...]

restart previously loaded static waveform

positional arguments:
  uut         uut  restart|stop

optional arguments:
  -h, --help  show this help message and exit
"""

import acq400_hapi
import os
import argparse
import threading
import time



def abort_action(uut, args):
    args.xwg_site.AWG_MODE_ABO = 1
    while acq400_hapi.Acq400.intpv(args.xwg_site.AWG_SHOT_COMPLETE) == 0:
        time.sleep(0.25)
    
 
def restart_action(uut, args):       
    pll = args.xwg_site.playloop_length
    args.xwg_site.playloop_length = "0 0"
    args.xwg_site.playloop_length = pll
    if args.auto_soft_trigger:
        while acq400_hapi.Acq400.intpv(args.xwg_site.AWG_ARM) == 0:
            time.sleep(0.25)
        uut.s0.soft_trigger = 1
    
    

def run_action(u):
    def _run_action():
        pass
      
parser = argparse.ArgumentParser(description='configure acq400_abort')
parser.add_argument('--test_loops', default=1, type=int, help="iterate in test mode for timing")
parser.add_argument('--auto_soft_trigger', default=0, type=int, help="1: fire soft trigger on restart")
parser.add_argument('--site', type=int, default=1, help="site with AWG")
parser.add_argument('uut', nargs=1, help="uut")
parser.add_argument('mode', nargs='+', help="mode restart|stop")

args = parser.parse_args()

uut = acq400_hapi.factory(args.uut[0])
args.xwg_site = uut.svc["s{}".format(args.site)]

for mode in args.mode:
    if mode == "restart":
        restart_action(uut, args)
    elif mode == "stop":
        abort_action(uut, args)
    elif mode == 'test':
        for ii in range(args.test_loops):
            abort_action(uut, args)
            restart_action(uut, args)
    else:
        print("sorry, bad mode, MUST be start|stop")
        exit(1)
