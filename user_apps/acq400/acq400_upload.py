#!/usr/bin/env python

"""
capture upload test
acq1001_capplot UUT1 [UUT2 ..]
where UUT1 is the ip-address or host name of first uut
example test client runs captures in a loop on one or more uuts

pre-requisite: UUT's are configured and ready to make a transient
capture
eg clk is running. soft trg enabled
eg transient length set.

runs one capture, uploads the data and plots with matplotlib
tested with 2 x 8 channels UUT's (ACQ1014)
matplot will get very congested with more channels.
this is really meant as a demonstration of capture, load to numpy,
it's not really intended as a scope UI.

usage: acq400_upload.py [-h] [--soft_trigger SOFT_TRIGGER]
                    [--trace_upload TRACE_UPLOAD] [--save_data SAVE_DATA]
                    [--plot_data PLOT_DATA] [--capture CAPTURE]
                    [--remote_trigger REMOTE_TRIGGER]
                    [--channels CHANNELS]
                    uuts [uuts ...]

acq400 upload

positional arguments:
  uuts                  uut[s]

optional arguments:
  -h, --help            show this help message and exit
  --soft_trigger SOFT_TRIGGER
                        help use soft trigger on capture
  --trace_upload TRACE_UPLOAD
                        1: verbose upload
  --save_data SAVE_DATA
                        store data to specified directory
  --plot_data PLOT_DATA
                        1: plot data
  --capture CAPTURE     1: capture data, 0: wait for someone else to capture,
                        -1: just upload
  --remote_trigger REMOTE_TRIGGER
                        your function to fire trigger
  --channels CHANNELS   comma separated channel list
"""

import sys
import acq400_hapi
import numpy as np

import os
import errno
import argparse
import re
import time

from subprocess import call

class ActionScript:
    def __init__(self, script_and_args):
        self.sas = script_and_args.split()
        print("ActionScript creates {}".format(self.sas))
    def __call__(self):
        print("ActionScript: call()")
        call(self.sas)

class WrtdAction:
    def __init__(self, master, max_triggers = 1):
        self.master = master
        self.max_triggers = max_triggers
    def __call__(self):
        self.master.s0.wrtd_tx = self.max_triggers

def set_shot(args, uuts):
    if args.shot != None:
        for u in uuts:
            u.s1.shot = args.shot

def upload(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    st = None

    acq400_hapi.cleanup.init()

    shot_controller = acq400_hapi.ShotControllerWithDataHandler(uuts, args)

    if args.wrtd_tx != 0:
        trigger_action = WrtdAction(uuts[0], args.wrtd_tx)
        for u in uuts:
            print("si5326_tune_phase on {}, this may take 30s".format(u.uut))
            u.s0.si5326_tune_phase = 1
    elif args.remote_trigger:
        trigger_action = ActionScript(args.remote_trigger)
    else:
        trigger_action = None
        st = SOFT_TRIGGER

    try:
        if args.capture == 0:
            state = '99'
            while state != '0':
                state = uuts[0].s0.state.split()[0]
                print("state:{}".format(state))
                if state == '1':
                    if trigger_action:
                        trigger_action()
                    elif st:
                        uut.s0.soft_trigger = '1'
                time.sleep(1)
            shot_controller.handle_data(args)
        else:
            set_shot(args, uuts)
            cap = 0
            while cap < args.capture:
                shot_controller.run_shot(soft_trigger = st, remote_trigger = trigger_action)
                cap += 1
            if args.capture == -1:
                shot_controller.handle_data(args)

    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")

SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
CAPTURE=int(os.getenv("CAPTURE", "0"))

def uniq(inp):
    out = []
    for x in inp:
        if x not in out:
            out.append(x)
    return out


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 upload')
    acq400_hapi.ShotControllerUI.add_args(parser)
    parser.add_argument('--soft_trigger', default=SOFT_TRIGGER, type=int, help="help use soft trigger on capture")
    parser.add_argument('--capture', default=CAPTURE, type=int, help="1: capture data, 0: wait for someone else to capture, -1: just upload")
    parser.add_argument('--remote_trigger', default=None, type=str, help="your function to fire trigger")
    parser.add_argument('--wrtd_tx', default=0, type=int, help="release a wrtd_tx when all boards read .. works when free-running trigger")
    parser.add_argument('uuts', nargs = '+', help="uut[s]")

    return parser.parse_args(argStr)


def run_main():
    args = get_args()
    # deduplicate (yes, some non-optimal apps call with duplicated uuts, wastes time)
    args.uuts = uniq(args.uuts)
    # encourage single ints to become a list
    if re.search(r'^\d$', args.channels) is not None:
        args.channels += ','
    args.shot = None

    upload(args)


# execution starts here

if __name__ == '__main__':
    run_main()
