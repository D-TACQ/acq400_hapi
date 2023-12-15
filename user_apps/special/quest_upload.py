#!/usr/bin/env python

"""quest upload test

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

example::

    ./quest_upload.py --POST=60000 --CLKDIV=100 --capture=1 --plot_data=0 \
--save_data=magdata_0001 --channels=1,2,3,4,32 192.168.1.210

.. rst-class:: hidden

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
    --soft_trigger SOFT_TRIGGER  help use soft trigger on capture
    --trace_upload TRACE_UPLOAD  1: verbose upload
    --save_data SAVE_DATA  store data to specified directory
    --plot_data PLOT_DATA  1: plot data
    --capture CAPTURE     1: capture data, 0: wait for someone else to capture, -1: just upload
    --remote_trigger REMOTE_TRIGGER  your function to fire trigger
    --channels CHANNELS   comma separated channel list
    --CLKDIV              set clock divider (10=1M)
    --POST                set number POST trigger samples
"""

import sys
import acq400_hapi
import numpy as np
try:
    import matplotlib.pyplot as plt
    plot_ok = 1
except RuntimeError as e:
    print("Sorry, plotting not available {}".format(e))
    plot_ok = 0

import os
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
        
def upload(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts] 
# assume one uut
    uut = uuts[0] 
    
    acq400_hapi.cleanup.init()

    shot_controller = acq400_hapi.ShotController(uuts)

    for u in uuts:
        if args.POST:
            u.s0.transient = "PRE=%d POST=%d SOFT_TRIGGER=%d" % (0, args.POST, 1)
        if args.CLKDIV:
            u.s1.CLKDIV = args.CLKDIV
        # make it EXT TRIGGER every time
        u.s1.TRG_DX = 'd0'
 
    if args.remote_trigger:
        trigger_action = ActionScript(args.remote_trigger)
        st = None
    else:
        trigger_action = None
        st = SOFT_TRIGGER
    try:  
        if args.capture > 0:
            shot_controller.run_shot(soft_trigger = st, remote_trigger = trigger_action)
        elif args.capture == 0:
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

        if args.trace_upload:
            for u in uuts:
                u.trace = 1
                        
        channel_set = eval(args.channels)
        chx, ncol, nchan, nsam = shot_controller.read_channels(channel_set)
     
        if args.save_data:
            volts = [ uut.chan2volts(channel_set[chn], chx[0][chn]) for chn in range(0,nchan) ]
            # save_data is the file name magdata_NNN
            with open("{}.csv".format(args.save_data), 'w') as fid:
                 for sample in range(0, nsam):
                     fid.write('%.6f,' % (sample*1e-6))
                     for chn in range(0, nchan):
#                     for chn in range(0, 2):
#                         fid.write({:4},'.format(volts[chn][sample]))
                         fid.write('%.4f%c' % ((volts[chn][sample]), ',' if chn < nchan-1 else '\n'))


# plot ex: 2 x 8 ncol=2 nchan=8
# U1 U2      FIG
# 11 21      1  2
# 12 22      3  4
# 13 23
# ...
# 18 28     15 16
        if plot_ok and args.plot_data:
            for col in range(ncol):
                for chn in range(0,nchan):
                    # channel index from 1 in API
                    volts = uut.chan2volts(chn+1, chx[col][chn])
                    fignum = 1 + col + chn*ncol
                    plt.subplot(nchan, ncol, fignum)                
                    plt.plot(volts)
                        
            plt.show()
            
    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")    
    
SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
TRACE_UPLOAD=int(os.getenv("TRACE_UPLOAD", "0"))
SAVEDATA=os.getenv("SAVEDATA", None)
PLOTDATA=int(os.getenv("PLOTDATA", "0"))
CAPTURE=int(os.getenv("CAPTURE", "0"))
CHANNELS=os.getenv("CHANNELS", "()")

def uniq(inp):
    out = []
    for x in inp:
        if x not in out:
            out.append(x)
    return out

def get_parser():
    parser = argparse.ArgumentParser(description='upload quest')  
    parser.add_argument('--soft_trigger', default=SOFT_TRIGGER, type=int, help="help use soft trigger on capture")
    parser.add_argument('--trace_upload', default=TRACE_UPLOAD, type=int, help="1: verbose upload")
    parser.add_argument('--save_data', default=SAVEDATA, type=str, help="store data to specified directory")
    parser.add_argument('--plot_data', default=PLOTDATA, type=int, help="1: plot data")
    parser.add_argument('--capture', default=CAPTURE, type=int, help="1: capture data, 0: wait for someone else to capture, -1: just upload")
    parser.add_argument('--remote_trigger', default=None, type=str, help="your function to fire trigger")
    parser.add_argument('--channels', default=CHANNELS, type=str, help="comma separated channel list")
    parser.add_argument('--CLKDIV', default=10, type=int, help="sample rate = 10MHz / CLKDIV")
    parser.add_argument('--POST', default=100000, type=int, help="set number of post-shot samples")
    parser.add_argument('uuts', nargs = '+', help="uut[s]")
    return parser

def run_main(args):
    # deduplicate (yes, some non-optimal apps call with duplicated uuts, wastes time)
    args.uuts = uniq(args.uuts)
    # encourage single ints to become a list
    if re.search(r'^\d$', args.channels) is not None:
        args.channels += ','
    upload(args)

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())




