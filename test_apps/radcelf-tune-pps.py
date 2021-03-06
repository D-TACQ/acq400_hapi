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

def web_message(message):
    print("web_message {} {}".format(type(message), message))
    with open('/dev/shm/radcelf-tune-pps.txt', 'w') as fd:
        for line in message.split('\n'):
            print("write {}".format(line))
            fd.write("{}\n".format(line))
        
def init(args): 
    uut = args.uut  
    print("configured clkdDB routing to source CLK from ddsC")
    uut.clkdB.CSPD = '02'
    uut.clkdB.UPDATE = '01'


    print("Initialise DDS C to a ratio of 1.0 for nominal 25 MHz")
    uut.s2.ddsC_upd_clk_fpga = '1'
    uut.ddsC.CR   = '004C0041'
    uut.ddsC.FTW1 = AD9854.ratio2ftw(1.0/12.0)
    time.sleep(30)
   
    

def control(args, prop_err, KPL):
    uut = args.uut
    ftw1 = args.uut.ddsC.FTW1
    xx = AD9854.ftw2ratio(ftw1)
    yy = xx - prop_err*KPL
    ftw1_yy = AD9854.ratio2ftw(yy)
    
    message = "fclk {} {}\nXX:{} ratio:{} - err:{} * KP:{} => yy:{} YY:{}".\
            format(args.fclk, "FINE" if args.fine else "INIT", ftw1, xx, prop_err, KPL, yy, ftw1_yy) 
    
    print(message)
    web_message(message)
      
    uut.s2.ddsC_upd_clk_fpga = '1'
    uut.ddsC.FTW1 = ftw1_yy
    uut.s2.ddsC_upd_clk_fpga = '0'
    
def process_last(args, line):   
# compute updated output based on error band return #secs to sleep. 
# NB: MUST not be too quick for the counter, which is itself quite slow..
    #print(line)
    mfdata = {}
    for pair in line.split():
        #print(pair)
        (key, value) = pair.split("=")
        mfdata[key] = float(value)
        
    err = mfdata['m1'] - args.fclk
    print("M1 error {}".format(err))
    if abs(err) > 1:
        print("control m1")
        control(args, err/args.fclk, KP)
        return 2

    err = mfdata['m10'] - args.fclk
    print("M10 error {}".format(err))
    if abs(err) > 0.2:
        print("control m10")
        control(args, err/args.fclk, KP*0.6)
        return 10

    err = mfdata['m30'] - args.fclk
    print("M30 error {}".format(err))
    if  abs(err) > 0.031:
        print("control m30")
        control(args, err/args.fclk, KP*0.4)
        return 30        

    err = mfdata['m100'] - args.fclk
    print("M100 error {}".format(err))
    if  abs(err) > 0.011:
        print("control m100")
        control(args, err/args.fclk, KP*0.25)
        return 100
    
    if args.fine:
        return 100
    
    print("TARGET Achieved, quitting...")
    exit(0)
               
        
def process(args):
    with open("/dev/shm/meanfreq.txt", "r") as mf:
        lines = mf.readlines()
        
    return process_last(args, lines[-1])
    
def radcelf_tune(args):
    while True:
        time.sleep(process(args))
    

def run_main():
    global KP
    parser = argparse.ArgumentParser("radcelf-tune-pps [fclk]")
    parser.add_argument('--best', default=True, help="select BEST clock for PPS sync")
    parser.add_argument('--fine', default=False, help="fine tune, runs forever")
    parser.add_argument('--Kp', default=0.05, type=float, help="Kp, proportional control constant" )
    parser.add_argument('fclk', nargs='*', default=[25000000], type=int, help="required clock frequency")
    args = parser.parse_args()
    fclk = args.fclk[0]
    KP = args.Kp
    message = "radcelf-tune-pps"
    if args.best:
        fbest =acq400_hapi.RAD3DDS.best_clock_pps_sync(fclk)
        if fbest != args.fclk:
            m2 = "Selected BEST clock {} => {}".format(fclk, fbest)
            print(m2)
            message = "{}\n{}".format(message, m2)
        fclk = fbest
    else:
        fclk = fclk
    args.fclk = fclk
    args.uut = acq400_hapi.RAD3DDS("localhost")
    
    web_message(message)
    
    if not args.fine:
        init(args)
        print("Starting Tuning")
        
    radcelf_tune(args)
        
# execution starts here


if __name__ == '__main__':
    run_main()
    
    