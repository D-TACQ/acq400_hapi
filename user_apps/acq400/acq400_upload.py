#!/usr/bin/env python3

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

example:
python3 ./user_apps/acq400/acq400_upload.py --post=100k --capture=1 --trace_upload=1 --plot_data=2 --channels=1,2,3,4 --trg=1,1,1 acq2106_339

--post=100k :: capture 100k samples, post trigger
--capture=1 :: capture
--trace_upload=1 :: observe upload timings (remove this)
--plot_data=2  :: plot data V vs time
--channels=1,2,3,4 :: plot 4 channels (plotter will struggle with many channels)
--trg=1,1,1   :: select soft trigger (default: front panel)
acq2106_339   :: UUT, DNS name


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

class EnableExtTrgAction:
    def __init__(self, master):
        self.master = master
        self.master.s0.SIG_SRC_TRG_0 = "NONE"
#        while int(float(self.master.s0.SIG_TRG_EXT_ACTIVE.split(" ")[1])) == 1:
        while acq400_hapi.activepv(self.master.s0.SIG_TRG_EXT_ACTIVE):
            time.sleep(.1)
        
    def __call__(self):
        self.master.s0.SIG_SRC_TRG_0 = "EXT"

class WrtdAction:
    def __init__(self, master, max_triggers = 1):
        self.master = master
        self.max_triggers = max_triggers
    def __call__(self):
        self.master.s0.wrtd_tx = self.max_triggers

class NetworkFgAction:
    def __init__(self, args, uut, dnsname):
        self.args = args
        self.uut = uut
        self.fg = acq400_hapi.Agilent33210A(dnsname)        
    def __call__(self):
        while acq400_hapi.intpv(self.uut.s0.TRANS_ACT_PRE) < self.args.pre:
            time.sleep(0.5)
        while self.uut.s1.event0 == '0,0,0':
            print("NetworkFgAction: snapped event disabled")
            time.sleep(0.5)
            
        print("TRIGGER")
        self.fg.trigger()


ST_DELAY=float(os.getenv("SOFT_TRIGGER_DELAY", "1.0"))

class EnableSoftSoftTrgAction:
    def __init__(self, args, uut):
        self.args = args
        self.uut = uut
        self.uut.s1.trg = '1,1,1'
        self.uut.s1.event0 = '1,1,1'
    def __call__(self):
        while acq400_hapi.intpv(self.uut.s0.TRANS_ACT_PRE) < self.args.pre:
            time.sleep(0.5)
        while self.uut.s1.event0 == '0,0,0':
            print("NetworkFgAction: snapped event disabled")
            time.sleep(0.5)
 
        time.sleep(ST_DELAY)
        print("SOFT EVENT TRIGGER")
        self.uut.s0.soft_trigger = '1'

 
def set_shot(args, uuts):
    if args.shot != None:
        for u in uuts:
            u.s1.shot = args.shot

@acq400_hapi.timing
def run_shot(args, uuts, shot_controller, trigger_action, st):
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



class TriggerCountLogger:
    knobs = ("SIG:TRG_EXT:", "SIG:TRG_MB:", "SIG:TRG_S1:")
    
    def __init__(self, uuts):
        self.uuts = uuts
        for u in uuts:
            for k in TriggerCountLogger.knobs:
                u.s0.sr("{}RESET=1".format(k))
        
    def __call__(self):
        results = []
        for u in self.uuts:
            for k in TriggerCountLogger.knobs:
                results.append(acq400_hapi.intpv(u.s0.sr("{}COUNT".format(k))))
                
        print("Trigger Check {} {}".format(results, "GOOD" if results[0]+results[1] == results[2] else "FAIL"))

class TimedShotController(acq400_hapi.ShotControllerWithDataHandler):
    @acq400_hapi.timing
    def handle_data(self, args):
        return super().handle_data(args)

    def __init__(self, _uuts, args, shot=None):
         super().__init__(_uuts, args, shot)
         
@acq400_hapi.timing
def upload(args, shots, doClose=False):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    [ acq400_hapi.Acq400UI.exec_args(uut, args) for uut in uuts ]
    st = None

    acq400_hapi.cleanup.init()
    if args.validate_triggers:
        tcl = TriggerCountLogger(uuts)
        
    for u in uuts:
        u.s0.TRANSIENT_SET_ABORT = '1'
    for u in uuts:
        while u.s0.TRANS_ACT_STATE.split(' ')[1] != 'IDLE':
            time.sleep(0.1)
          
    shot_controller = TimedShotController(uuts, args)

    if args.wrtd_tx != 0:
        trigger_action = WrtdAction(uuts[0], args.wrtd_tx)
        for u in uuts:
            print("si5326_tune_phase on {}, this may take 30s".format(u.uut))
            u.s0.si5326_tune_phase = 1
    elif args.sig_gen:
        trigger_action = NetworkFgAction(args, uuts[0], args.sig_gen)
    elif args.remote_trigger:
        trigger_action = EnableExtTrgAction(uuts[0])
    elif args.soft_soft:
        print("setting soft_soft trigger condition")
        trigger_action = EnableSoftSoftTrgAction(args, uuts[0])
    else:
        trigger_action = None
        st = args.soft_trigger

    for shot in range(shots):
        print("host shot {} uut shot {}".format(shot, uuts[0].s0.shot))
        try:
            run_shot(args, uuts, shot_controller, trigger_action, st)
        except acq400_hapi.acq400.DataNotAvailableError:
            print("DataNotAvailableError pick up RAW data and exit")
            for u in uuts:  
                u.read_chan(0)
                rawfn = "{}/{}_CH00".format(args.save_data, u.uut)              
                print("RAW DATA {} size {}".format(rawfn, os.stat(rawfn).st_size))
            
        if args.validate_triggers:
            tcl()      
    
    if shots > 1:
        for u in uuts:
            print("Search Stats: {} ROI {} ALL {}".format(u.uut, u.statmon.search_roi_count, u.statmon.search_all_count))   
    if doClose:
        for u in uuts:
            u.close()

SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
CAPTURE=int(os.getenv("CAPTURE", "0"))

def uniq(inp):
    out = []
    for x in inp:
        if x not in out:
            out.append(x)
    return out


def get_parser(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 upload')
    acq400_hapi.ShotControllerUI.add_args(parser)
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    parser.add_argument('--soft_trigger', default=SOFT_TRIGGER, type=int, help="help use soft trigger on capture")
    parser.add_argument('--capture', default=CAPTURE, type=int, help="1: capture data, 0: wait for someone else to capture, -1: just upload")
    parser.add_argument('--remote_trigger', default=None, type=str, help="options: EXT")
    parser.add_argument('--wrtd_tx', default=0, type=int, help="release a wrtd_tx when all boards read .. works when free-running trigger")    
    parser.add_argument('--shots', default=1, type=int, help="number of shots to run")
    parser.add_argument('--newobjectsplease', default=0, type=int, help="create new object instantiations every run")
    parser.add_argument('--sig_gen', default=None, type=str,
                        help='Network of Agilent 33210A or equivalent.') 
    parser.add_argument('--soft_soft', default=None, type=str,
                        help='double soft trigger, first a start trig, then a pre->post event trig')
    parser.add_argument('--validate_triggers', default=0, type=int, help="check trigger counts after each shot")   
    parser.add_argument('uuts', nargs = '+', help="uut[s]")
    return parser

@acq400_hapi.timing
def run_main(args):    
    # deduplicate (yes, some non-optimal apps call with duplicated uuts, wastes time)
    args.uuts = uniq(args.uuts)
    # encourage single ints to become a list
    if re.search(r'^\d$', args.channels) is not None:
        args.channels += ','
    args.shot = None
    if args.newobjectsplease:
        for shot in range(args.shots):
            upload(args, 1, doClose=True)
    else:
        upload(args, args.shots)

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())
