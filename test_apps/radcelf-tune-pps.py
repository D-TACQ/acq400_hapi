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

def control(prop_err):
    ftw1 = uut.ddsC.FTW1
    xx = AD9854.ftw2ratio(ftw1)
    yy = xx - prop_err*KP
    ftw1_yy = AD9854.ratio2ftw(yy)
    
    print("XX:{} ratio:{} - err:{} * KP:{} => yy:{} YY:{}".format(ftw1, xx, prop_err, KP, yy, ftw1_yy))
    
    uut.s2.ddsC_upd_clk_fpga = '1'
    uut.ddsC.FTW1 = ftw1_yy
    uut.s2.ddsC_upd_clk_fpga = '0'
    
def process_last(line):
# compute updated output based on error band return #secs to sleep. 
# NB: MUST not be too quick for the counter, which is itself quite slow..
    #print(line)
    mfdata = {}
    for pair in line.split():
        #print(pair)
        (key, value) = pair.split("=")
        mfdata[key] = float(value)
        
    err = mfdata['m1'] - TARGET
    
    if abs(err) > 2:
        print("control m1")
        control(err/TARGET)
        return 3
    
    err = mfdata['m10'] - TARGET
    if abs(err) > 0.2 and abs(err) < 2:
        print("control m10")
        control(err/TARGET)
        return 10
    
    err = mfdata['m100'] - TARGET
    if  abs(err) > 0.02 and abs(err) < 0.2:
        print("control m100")
        control(err/TARGET)
        return 100
    
    print("TARGET Achieved, quitting...")
    exit(0)
               
        
def process():
    with open("/dev/shm/meanfreq.txt", "r") as mf:
        lines = mf.readlines()
        
    return process_last(lines[-1])
    
while True:
    time.sleep(process())
    
