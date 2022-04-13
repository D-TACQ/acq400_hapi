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



def stop_action(uut, args, xwg_site):
    xwg_site.AWG_MODE_ABO = 1
    while acq400_hapi.Acq400.intpv(xwg_site.AWG_SHOT_COMPLETE) == 0:
        time.sleep(0.25)

def start_action(uut, args, xwg_site):    
    pll = xwg_site.playloop_length
    xwg_site.playloop_length = "0 0"
    xwg_site.playloop_length = pll
    if args.auto_soft_trigger:
        while acq400_hapi.Acq400.intpv(xwg_site.AWG_ARM) == 0:
            time.sleep(0.25)
        uut.s0.soft_trigger = 1

    

def run_action(u):
    def _run_action():
        pass
      
parser = argparse.ArgumentParser(description='configure acq400_abort')
parser.add_argument('--auto_soft_trigger', default=0, type=int, help="1: fire soft trigger on restart")
parser.add_argument('--site', type=int, default=1, help="site with AWG")
parser.add_argument('--mode', default='stop', help="mode start|stop")
parser.add_argument('uut', nargs='+', help="uut [uut2...]")


args = parser.parse_args()

uuts = [ acq400_hapi.factory(u) for u in args.uut ]

for u in uuts:
    xwg_site = u.svc["s{}".format(args.site)]

    if args.mode == "start":
        start_action(u, args, xwg_site)
    else:
        stop_action(u, args, xwg_site)
