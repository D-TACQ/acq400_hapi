#!/usr/bin/env python

""" radcelf-chirp-init - set up a chirp ..
    radcelf-chirp-init UUT1
    where UUT1 is the ip-address or host name of the uut
    powerful alternative to embedded shell script.

    no ssh keys or remote execution, nfs mounts required.

    potential enhancements stepping stone to avoid the magic numbers:
    eg
            AD9854.CR.X4 = 00040000
    potential to program real numbers eg
      >>> format(long(0.5 * pow(2,48)), '012x')
     '800000000000'

    seamless integration with data capture (and maybe postprocess and analysis..)
"""

import sys
import acq400_hapi
import argparse
import time


# AD9854 class in the making ..
def FTW1(ratio):
    return format(long(ratio * pow(2,48)), '012x')

def set_upd_clk_fpga(uut, idds, value):
    if idds == 0:
        uut.s2.ddsA_upd_clk_fpga = value
    else:
        uut.s2.ddsB_upd_clk_fpga = value

def freq(sig):
    return float(sig.split(" ")[1])

def init_chirp(uut, idds):
# SETTING KAKA'AKOS CHIRP
#
# Set AD9854 clock remap to 25 MHz
    dds = uut.ddsA if idds == 0 else uut.ddsB

    uut.ddsC.CR     = '004C0041'
    uut.ddsC.FTW1   = FTW1(1.0/12.0)

# Program AD9512 secondary clock to choose 25 MHz from the AD9854 remap
    uut.clkdB.CSPD  = '02'
    uut.clkdB.UPDATE = '01'


# Program the chirp using Kaka'ako parameters
    set_upd_clk_fpga(uut, idds, '1')
    dds.CR     = '004C0061'
    dds.FTW1   = '172B020C49BA'
    dds.DFR    = '0000000021D1'
    dds.UCR    = '01F01FD0'
    dds.RRCR   = '000001'
    dds.IPDMR  = '0FFF'
    dds.QPDMR  = '0FFF'
    dds.CR     = '004C8761'
    set_upd_clk_fpga(uut, idds, '0')

# Set the trigger
# lera_acq_setup
# we assume a 25MHz from ddsC
# trigger from site 3 ddsA
    try:
	uut.s1.trg  = '1,3,1'
	uut.s1.clk  = '1,3,1'
	uut.s1.hi_res_mode = '1'
# 25 MHz/4 = 6.25MHz / 512 = SR 12207
	uut.s1.CLKDIV   = '4'
    except:
        print "ACQ435 not fitted"



def valid_chirp(freq):
    return freq >= 4 or freq <= 5

def verify_chirp(uut, test):
    retry = 0
    
    while retry < 10:
        if valid_chirp(freq(uut.s0.SIG_TRG_S2_FREQ)) and valid_chirp(freq(uut.s0.SIG_TRG_S3_FREQ)):
            print("test:%d  PASS %s %s" % (test, uut.s0.SIG_TRG_S2_FREQ, uut.s0.SIG_TRG_S3_FREQ))
            return True
        else:
            time.sleep(1)
            retry = retry + 1
            
    return False
        
def run_test(args):
    uut = acq400_hapi.RAD3DDS(args.uut[0])
    
    for test in range(0, args.test):
        uut.s2.RADCELF_init = 1
        init_chirp(uut, 0)
        init_chirp(uut, 1)
        verify_chirp(uut, test)
    
def run_main():  
    parser = argparse.ArgumentParser(description='radcelf-chirp-init')
    parser.add_argument('--test', default=1, type=int, help="set number of tests to run")
    parser.add_argument('uut', nargs=1, help="uut")
    run_test(parser.parse_args())
    
# execution starts here

if __name__ == '__main__':
    run_main()
