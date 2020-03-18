#!/usr/bin/env python

"""
configure and run White Rabbit Pulse Generator on uut

./load_wrpg_stl.py --stl=file uut


WRTD: White Rabbit Trigger Distribution
WRTT: White Rabbit Time Trigger.
WRPG: White Rabbit Pulse Generator


Ext-Trg -> WRTD -> WRTT -> WRPG

WRTD detects an external trigger input, snaps the TAI time, broadcasts a WRTD message for a short time in the future (50ms).
When the specified TAI time is reached, all ACQ2106 units issue pulse WRTT
We set up the WRPG to trigger on the WRTT



Full sequence:

    1. Activate package 99-custom_wrpg

mv /mnt/packages.opt/99-custom_wrpg* /mnt/packages
sync;sync;reboot

    2. A standard ACQ2106_WR box boots with WRTD running

We typically connect a 2Hz signal to the WRTD INPUT port.
Check it's running: 2Hz count on TRG.d0

    3. Actually, a free-running trigger is NOT helpful, stop it

If you have active control of the WRTD INPUT, stop the signal
Else, it's easy to stop the WRTTD output by stopping the wrtd rx process:

nc localhost 4280
^T
^X

Check that the 2Hz clock on TRG.d0 stops.

   4. Configure a transient capture to trigger on TRG.d0

From cs-studio:
    Capture|Transient [DEFAULT POST] [setMode] ARM
    The ADC sits in ARM mode.
Or use an external client program. Ensure that
    UUT:1:TRG=enable UUT:1:TRG:DX=d0 UUT:1:TRG:SENSE=rising

Set a waterfall display: 
    /usr/local/epics/scripts/set.AI.waterfall

   5. Configure the GPG to use TRG.d0
    ACQ400GPG.OPI | set GPG_TRG
Or use an external client program. Ensure that
    UUT:0:GPG_TRG=enable UUT:0:GPG_TRG:DX=d0 UUT:0:GPG_TRG:SENSE=rising

   6. Load the STL, using this program

./load_wrpg_stl.py --stl=STL/ramp_1step_64samp.stl uut

   7 Enable the WRTD INPUT.

^X again on the 4280 session will allow the WRTT signal to restart.

Both the GPG and the ADC will trigger on the next WRTT, and at the end of the shot you should see the preprogrammed pulse train.

Limits:

1. Number of DO lines: 32 (Single DIO482 in Site 6)
2. Time resolution: 1usec (clocks on WR 1MHz)
3. Maximum number of states: 512
4. Maximum delay per state: 2^24 = 16s
5. Maximum theoretical delay: > 8192s with 1usec resolution.

In practise, we don't expect delays > 600s.

"""

import acq400_hapi
import argparse
import sys

def load_stl_file(uut, stl_file):
    with open(stl_file, 'r') as fp:
        uut.load_wrpg(fp.read(), uut.s0.trace)

class SendsWrtd:
    def __init__(self, uut):
        self.uut = uut
    def __call__(self):
        self.uut.s0.wrtd_tx_immediate='1'

class EnablesWrtt:
    def __init__ (self, uut):
        self.uut = uut
    def __call__ (self):
        self.uut.s0.SIG_SRC_TRG_0 = 'WRTT'

def tee_shots(args, uut, shot):
    uut.s1.shot = shot    
    uut.s0.SIG_SRC_TRG_0 = 'HOSTB'  # gate external trigger OFF
    uut.s0.GPG_TRG = 'external'
    uut.s0.GPG_TRG_DX = 'd0'
    uut.s0.GPG_TRG_SENSE = 'rising'
    uut.s0.transient= 'POST=100000'
    uut.s1.TRG = 'external'
    uut.s1.TRG_DX = 'd0'
    uut.s1.TRG_SENSE = 'rising'

def run_wrpg(args):
    uut = acq400_hapi.acq400.Acq400(args.uut[0])
    if args.shots > 0:
	shot = 0
	tee_shots(args, uut, shot)
        
        shot_controller = acq400_hapi.ShotController([uut])
        while shot < args.shots:
            load_stl_file(uut, args.stl)
	    rt = SendsWrtd(uut) if args.trg == 'WrtdImmediate' else EnablesWrtt(uut)
            shot_controller.run_shot(remote_trigger=rt)
            shot = shot + 1
    else:
        load_stl_file(uut, args.stl)

def run_main():
    parser = argparse.ArgumentParser(description="load_wrpg_stl")
    parser.add_argument('--stl', default='none', type=str, help='stl file')
    parser.add_argument('--trg', default='"WrtdImmediate', help="shot trigger: WrtdImmediate or WRTT")
    parser.add_argument('--shots', default=0, type=int, help='run a series of shots, with immediate trigger')
    parser.add_argument('uut', nargs=1, help="uut")
    run_wrpg(parser.parse_args())



# execution starts here

if __name__ == '__main__':
    run_main()



