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

def init(fclk):
    uut = acq400_hapi.RAD3DDS("localhost")
    print("configured clkdDB routing to source CLK from ddsC")
    uut.clkdB.CSPD = '02'
    uut.clkdB.UPDATE = '01'


    print("Initialise DDS C to a ratio of 1.0 for nominal 25 MHz")
    uut.s2.ddsC_upd_clk_fpga = '1'
    uut.ddsC.CR   = '004C0041'
    uut.ddsC.FTW1 = AD9854.ratio2ftw(1.0/12.0)
    time.sleep(30)
    print("Starting Tuning")
    return uut

def control(uut, fclk, prop_err, KPL):
    ftw1 = uut.ddsC.FTW1
    xx = AD9854.ftw2ratio(ftw1)
    yy = xx - prop_err*KPL
    ftw1_yy = AD9854.ratio2ftw(yy)
    
    message = "fclk {}\nXX:{} ratio:{} - err:{} * KP:{} => yy:{} YY:{}".
            format(fclk, ftw1, xx, prop_err, KPL, yy, ftw1_yy) 
    
    print(message)
    
    with open('/dev/shm/radcelf-tune-pps.txt', 'w') as fd:
            fd.write("{}\n".format(message))
  
    uut.s2.ddsC_upd_clk_fpga = '1'
    uut.ddsC.FTW1 = ftw1_yy
    uut.s2.ddsC_upd_clk_fpga = '0'
    
def process_last(uut, line, fclk, fine):
# compute updated output based on error band return #secs to sleep. 
# NB: MUST not be too quick for the counter, which is itself quite slow..
    #print(line)
    mfdata = {}
    for pair in line.split():
        #print(pair)
        (key, value) = pair.split("=")
        mfdata[key] = float(value)
        
    err = mfdata['m1'] - TARGET
    print("M1 error {}".format(err))
    if abs(err) > 1:
        print("control m1")
        control(uut, fclk, err/TARGET, KP)
        return 2

    err = mfdata['m10'] - TARGET
    print("M10 error {}".format(err))
    if abs(err) > 0.2:
        print("control m10")
        control(uut, fclk, err/TARGET, KP*0.6)
        return 10

    err = mfdata['m30'] - TARGET
    print("M30 error {}".format(err))
    if  abs(err) > 0.031:
        print("control m30")
        control(uut, fclk, err/TARGET, KP*0.4)
        return 30        

    err = mfdata['m100'] - TARGET
    print("M100 error {}".format(err))
    if  abs(err) > 0.011:
        print("control m100")
        control(uut, fclk, err/TARGET, KP*0.25)
        return 100
    
    if fine:
        return 100
    
    print("TARGET Achieved, quitting...")
    exit(0)
               
        
def process(uut, fclk):
    with open("/dev/shm/meanfreq.txt", "r") as mf:
        lines = mf.readlines()
        
    return process_last(uut, lines[-1], fclk)
    
def radcelf_tune(fclk, fine):
    uut = init(fclk)
    TARGET = fclk
    while True:
        time.sleep(process(uut, fclk, fine))
    

def run_main():
    parser = argparse.ArgumentParser("radcelf-tune-pps [fclk]")
    parser.add_argument('--best', default=True, help="select BEST clock for PPS sync")
    parser.add_argument('--fine', default=False, help="fine tune, runs forever")
    parser.add_argument('--Kp', default=0.05, type=float, help="Kp, proportional control constant" )
    parser.add_argument('fclk', nargs='*', default=[25000000], type=int, help="required clock frequency")
    args = parser.parse_args()
    fclk = args.fclk[0]
    KP = args.Kp
    if args.best:
        fbest =acq400_hapi.RAD3DDS.best_clock_pps_sync(fclk)
        if fbest != args.fclk:
            print("Selected BEST clock {} => {}".format(fclk, fbest))
        fclk = fbest
    else:
        fclk = fclk
    radcelf_tune(fclk. args.fine)
        
# execution starts here


if __name__ == '__main__':
    run_main()
    
    