#!/usr/bin/env python

""" radcelf-freq-test - iterate a set of frequencies with self-test0

"""

import sys
import acq400_hapi
import argparse
import time
from builtins import int


# AD9854 class in the making ..
def FTW1(ratio):
    return format(int(ratio * pow(2,48)), '012x')

def set_upd_clk_fpga(uut, idds, value):
    if idds == 0:
        uut.s2.ddsA_upd_clk_fpga = value
    else:
        uut.s2.ddsB_upd_clk_fpga = value

def freq(sig):
    return float(sig.split(" ")[1])

FINT = float(300000000)
CMULT = 12.0
DBG = 0

def init_clk(uut):
    global FINT
# Set AD9854 clock remap to 25 MHz
    uut.ddsC.CR     = '004C0041'
    uut.ddsC.FTW1   = FTW1(1.0/CMULT)
# Program AD9512 secondary clock to choose 25 MHz from the AD9854 remap
    uut.clkdB.CSPD  = '02'
    uut.clkdB.UPDATE = '01'
    print("sleep 10 for FINT stabilization")
    time.sleep(10)
    FINT=round(freq(uut.s2.SIG_DDS_INP_FREQ)*CMULT, 4)
    print("Using FINT=%.3e" % FINT)
    
    
def set_freq(uut, dds, freq):
    global FINT 
    global DBG
# X12, SINC off    
    dds.CR   = '004C0041'
    dds.FTW1 = FTW1(freq/FINT)
    if DBG:
        print("set_freq %s %.3e FINT %.3e FTW1 %s" % ("ddsA" if uut.ddsA == dds else "ddsB",
                                                      freq, FINT, FTW1(freq/FINT)))


def valid_freq(actual, target):    
    return abs(float(actual) - float(target)) < 100000

def verify_freq(uut, test, freqA, freqB):
    retry = 0
    
    while retry < 10:
        if valid_freq(freq(uut.s2.SIG_DDS_A_FREQ), freqA) and valid_freq(freq(uut.s2.SIG_DDS_B_FREQ), freqB):
            print("test:%d  PASS %s %s" % (test, freq(uut.s2.SIG_DDS_A_FREQ), freq(uut.s2.SIG_DDS_B_FREQ)))
            return True
        else:
            time.sleep(1)
            retry = retry + 1
            
    print("test:%d FAIL %s != %s %s != %s" % (test, freqA, freq(uut.s2.SIG_DDS_A_FREQ), freqB, freq(uut.s2.SIG_DDS_B_FREQ)))
    return False
    
FREQS_MHz = [ 13, 17, 19, 23, 29, 31 ]    

def next_freq(f):
    global FREQS_MHz
    for fx in FREQS_MHz:
        if fx > f:
            return fx
        
    return FREQS_MHz[0]
    
    
def run_test(args):
    global FREQS_MHz
    global DBG
    DBG = args.debug
    uut = acq400_hapi.RAD3DDS(args.uut[0])
    
    uut.s2.RADCELF_init = 1
    init_clk(uut)
    set_upd_clk_fpga(uut, 0, '1')
    set_upd_clk_fpga(uut, 1, '1')
    
    for test in range(0, args.test):        
        for f in FREQS_MHz:
            fA = f*1000000
            fB = next_freq(f)*1000000
            
            set_freq(uut, uut.ddsA, fA)
            set_freq(uut, uut.ddsB, fB)
            
            verify_freq(uut, test, fA, fB)
    
def run_main():  
    parser = argparse.ArgumentParser(description='radcelf-chirp-init')
    parser.add_argument('--test', default=1, type=int, help="set number of tests to run")
    parser.add_argument('--debug', default=0, type=int, help="set number of tests to run")
    parser.add_argument('uut', nargs=1, help="uut")
    run_test(parser.parse_args())
    
# execution starts here

if __name__ == '__main__':
    run_main()
