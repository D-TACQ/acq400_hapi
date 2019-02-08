#!/usr/bin/env python
""" bolo8_cal_cap_loop.py ..
run a bolo8 calibration, store to MDSplus ODD shot
run a bolo8 capture, store to MDSplus EVEN shot
ASSUME : each uut has a tree of the same name
Script calls into MDSplus to increment shots, so it MUST run on the MDSplus server

Usage
./bolo8_cal_cap_loop.py --shots=1 acq2106_059
run one cal, one capture
./bolo8_cal_cap_loop.py --shots=100 acq2106_059
run 100 cal/captures

./bolo8_cal_cap_loop.py --cap=0 --shots=1 acq2106_059
run one cal
./bolo8_cal_cap_loop.py --cal=0 --shots=100 acq2106_059
run 100 captures

sage: bolo8_cal_cap_loop.py [-h] [--cap CAP] [--cal CAL] [--post POST]
                             [--clk CLK] [--trg TRG] [--shots SHOTS]
                             uuts [uuts ...]

bolo8_cal_cap_loop

positional arguments:
  uuts           uut list

optional arguments:
  -h, --help     show this help message and exit
  --cap CAP      capture
  --cal CAL      calibrate
  --post POST    post trigger length
  --clk CLK      clk "int|ext SR [CR]"
  --trg TRG      trg "int|ext rising|falling"
  --shots SHOTS  set number of shots [1]

"""


import sys
import os
import acq400_hapi
import argparse
import time
USING_MDSPLUS=0

if USING_MDSPLUS:
    from MDSplus import *

def odd(n):
    return n%2 == 1

def even(n):
    return n%2 == 0

__shot = 0
def null_set_next_shot(args, flavour, info):
    global __shot
    __shot += 1
    return __shot

def mds_set_next_shot(args, flavour, info):
    old_shots = [Tree.getCurrent(u) for u in args.uuts]
    sn = max(old_shots) + 1
    # this is only going to run once
    while not flavour(sn):
        sn += 1
    for tree in args.uuts:
        print("Setting {} for {} to shot {}".format(tree, info, sn))
        Tree.setCurrent(tree, sn)
        Tree(tree, -1).createPulse(sn)
    return sn


if USING_MDSPLUS:
    set_next_shot = mds_set_next_shot
else:
    set_next_shot = null_set_next_shot

def run_cal1(uut, shot):
    txt = uut.run_service(acq400_hapi.AcqPorts.BOLO8_CAL, eof="END")
    logfile = "{}/cal_{}.log".format(os.getenv("{}_path".format(uut.uut), "."), shot)
    try:
        with open(logfile, 'w') as log:
            print("logging to {}".format(logfile))
            log.write(txt)
    except IOError as e:
        logfile = "./cal_{}.log".format(shot)
        with open(logfile, 'w') as log:
            print("logging to {}".format(logfile))
            log.write(txt)




def run_cal(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    for u in uuts:
        # trg=1,1,1 external d1 RISING
        u.old_trg = u.s1.trg.split(' ')[0].split('=')[1]
        u.s1.trg = "1,1,1" # Set soft trigger for calibration.
    shot = set_next_shot(args, odd, "Cal")
    # hmm, running the cal serialised?. not cool, parallelize me ..
    for u in uuts:
        run_cal1(u, shot)
    # unfortunately this sleep seems to be necessary, else subsequent shot HANGS at 21760
    time.sleep(2)
    for u in uuts:
        u.s1.trg = u.old_trg

    if args.single_calibration_only == 1:
        shot = set_next_shot(args, even, "Cap")


def run_capture(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    shot = set_next_shot(args, even, "Cap")

    for u in uuts:
        u.s0.transient = "POST={} SOFT_TRIGGER=0".format(args.post)
        if args.trg == "ext rising" or args.trg == "ext":
            u.s1.trg = "1,0,1"
        elif  args.trg == "ext falling":
            u.s1.trg = "1,0,0"

    for u in uuts:
        u.s0.set_arm = '1'

    for u in uuts:
        u.statmon.wait_armed()

    if args.trg == "int":
        # again, not really parallel
        for u in uuts:
            print("trigger")
            u.s0.soft_trigger = '1'

    for u in uuts:
        u.statmon.wait_stopped()


def run_shots(args):

    for shot in range(1, args.shots+1):
        print("Cycle {}".format(shot))
        if args.cal:
            run_cal(args)
        if args.cap:
            run_capture(args)


def run_main():
    parser = argparse.ArgumentParser(description='bolo8_cal_cap_loop')
    parser.add_argument('--cap', default=1, type=int, help="capture")
    parser.add_argument('--cal', default=1, type=int, help="calibrate")
    parser.add_argument('--single_calibration_only', default=0, type=int, help="run one calibration shot only")
    parser.add_argument('--post', default=100000, help="post trigger length")
    parser.add_argument('--clk', default="int 1000000", help='clk "int|ext SR [CR]"')
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('--shots', default=1, type=int, help='set number of shots [1]')
    parser.add_argument('uuts', nargs='+', help="uut list")
    args = parser.parse_args()
    if args.single_calibration_only == 1:
        print("setting single calibration mode, overwrites other settings")
        args.cap = 0
        args.cal = 1
        args.shots = 1

    run_shots(args)


# execution starts here

if __name__ == '__main__':
    run_main()
