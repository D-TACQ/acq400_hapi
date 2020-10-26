#!/usr/bin/env python
'''
Created on 21 Sep 2020

@author: pgm

radcelf-tune-pps 
reads meanfreq output from ppsmon
uses error from m1, m10, m100 for proportional control

KPROP=0.05  : 0.5 was unstable. Must be some error in my calcs, but this does converge well
'''

import sys
import acq400_hapi
from acq400_hapi import AD9854
import argparse
import time
from builtins import int

TARGET=25000000.00
KP=0.05

uut = acq400_hapi.RAD3DDS("localhost")
time.sleep(50)


def control(prop_err,KPL):
    ftw1 = uut.ddsC.FTW1
    xx = AD9854.ftw2ratio(ftw1)
    yy = xx - prop_err*KPL
    ftw1_yy = AD9854.ratio2ftw(yy)
    
    print("XX:{} ratio:{} - err:{} * KP:{} => yy:{} YY:{}".format(ftw1, xx, prop_err, KPL, yy, ftw1_yy))
    
    uut.s2.ddsC_upd_clk_fpga = '1'
    uut.ddsC.FTW1 = ftw1_yy
    uut.s2.ddsC_upd_clk_fpga = '0'
    uut.s0.spad2 = ftw1_yy[4:]             # write low 4 bytes to spad2 for in-data signaling
    
def process_last(line):
# compute updated output based on error band return #secs to sleep. 
# NB: MUST not be too quick for the counter, which is itself quite slow..
    #print(line)
    mfdata = {}
    for pair in line.split():
        #print(pair)
        (key, value) = pair.split("=")
        mfdata[key] = float(value)
        

    err = mfdata['m100'] - TARGET
    print("M100 error {}".format(err))
    print("control m100")
    control(err/TARGET, KP*0.25)
    return 100

def process():
    with open("/dev/shm/meanfreq.txt", "r") as mf:
        lines = mf.readlines()
        
    return process_last(lines[-1])
    
def radcelf_tune(fclk):
    TARGET = fclk
    while True:
        time.sleep(process())
    

def run_main():
    parser = argparse.ArgumentParser("radcelf-tune-pps [fclk]")
    parser.add_argument('--best', default=True, help="select BEST clock for PPS sync")
    parser.add_argument('--Kp', default=0.05, type=float, help="Kp, proportional control constant" )
    parser.add_argument('fclk', nargs=1, default=25000000, type=int, help="required clock frequency")
    args = parser.parse_args()
    KP = args.kp
    if args.best:
        fbest =acq400_hapi.RAD3DDS.best_clock_pps_sync(args.fclk)
        if fbest != args.fclk:
            print("Selected BEST clock {} => {}".format(args.fclk, fbest))
        fclk = fbest
    else:
        fclk = args.fclk
    radcelf_tune(fclk)