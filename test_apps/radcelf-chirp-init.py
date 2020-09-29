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
from builtins import int
from acq400_hapi import AD9854 
from acq400_hapi import Debugger


    
    
def set_upd_clk_fpga(uut, idds, value):
    if idds == 0:
        uut.s2.ddsA_upd_clk_fpga = value
    else:
        uut.s2.ddsB_upd_clk_fpga = value


def freq(sig):
    return float(sig.split(" ")[1])


@Debugger
def init_remapper(uut):
# Set AD9854 clock remap to 25 MHz
    uut.ddsC.CR = '004C0041'
    uut.ddsC.FTW1 = AD9854.ratio2ftw(1.0/12.0)

# Program AD9512 secondary clock to choose 25 MHz from the AD9854 remap
    uut.clkdB.CSPD = '02'
    uut.clkdB.UPDATE = '01'

@Debugger        
def init_chirp(uut, idds):
    # SETTING KAKA'AKOS CHIRP
    #
    dds = uut.ddsA if idds == 0 else uut.ddsB

# Program the chirp using Kaka'ako parameters
    set_upd_clk_fpga(uut, idds, '1')
    dds.CR = '004C0061'
    dds.FTW1 = '172B020C49BA'
    dds.DFR = '0000000021D1'
    dds.UCR = '01F01FD0'
    dds.RRCR = '000001'
    dds.IPDMR = '0FFF'
    dds.QPDMR = '0FFF'
    dds.CR = '004C8761'
    set_upd_clk_fpga(uut, idds, '0')

@Debugger
def init_trigger(uut):
# Set the trigger
# lera_acq_setup
# we assume a 25MHz from ddsC
# trigger from site 3 ddsA
    try:
        uut.s1.trg = '1,3,1'
        uut.s1.clk = '1,3,1'
        uut.s1.hi_res_mode = '1'
# 25 MHz/4 = 6.25MHz / 512 = SR 12207
        uut.s1.CLKDIV = '4'
    except:
        print("ACQ435 not fitted")


GPS_SYNC_DDSA = 0x1
GPS_SYNC_DDSB = 0x2
GPS_SYNC_DDSX = 0x3

def _gps_sync(dds, gps_sync_chirp_en, hold_en):
    if gps_sync_chirp_en:
        dds.gps_sync_chirp = 1
        if hold_en:
            dds.gps_engage_hold = 1
            # dds_gps_arm_pps executed later
        else:
            dds.gps_arm_pps = 0
            dds.gps_engage_hold = 0
    else:
        dds.gps_sync_chirp = 0
@Debugger
def gps_sync(uut, ddsX=GPS_SYNC_DDSX, gps_sync_chirp_en=False, hold_en=False):
    if ddsX&GPS_SYNC_DDSA:
        _gps_sync(uut.ddsA, gps_sync_chirp_en, hold_en)
    if ddsX&GPS_SYNC_DDSB:
        _gps_sync(uut.ddsB, gps_sync_chirp_en, hold_en)

        
  
@Debugger
def radcelf_init(uut, legacy):
    if legacy:
        uut.s2.RADCELF_init = 1
    else:
        uut.radcelf_init()
    
@Debugger
def reset_counters(uut):  
    uut.s0.SIG_TRG_S2_RESET = 1
    uut.s0.SIG_TRG_S3_RESET = 1    

def valid_chirp(freq):
    return freq >= 4 or freq <= 5


def verify_chirp(uut, test):
    retry = 0

    while retry < 10:
        if valid_chirp(freq(uut.s0.SIG_TRG_S2_FREQ)) and valid_chirp(freq(uut.s0.SIG_TRG_S3_FREQ)):
            print("test:%d  PASS %s %s" %
                  (test, uut.s0.SIG_TRG_S2_FREQ, uut.s0.SIG_TRG_S3_FREQ))
            return True
        else:
            time.sleep(1)
            retry = retry + 1

    return False


def init_dual_chirp(args, uut):
    gps_sync(uut, gps_sync_chirp_en=False)
    radcelf_init(uut, args.legacy_radcelf_init)
    gps_sync(uut, gps_sync_chirp_en=args.gps_sync)
    reset_counters(uut)
    if args.noinitremapper == 0:
        init_remapper(uut)    
    gps_sync(uut, gps_sync_chirp_en=args.gps_sync, hold_en=True)
    init_chirp(uut, 0)
    init_chirp(uut, 1)
    gps_sync(uut, gps_sync_chirp_en=args.gps_sync)
    init_trigger(uut)

        
def run_test(args):
    uuts = [acq400_hapi.RAD3DDS(u) for u in args.uuts]

    for test in range(0, args.test):
        for uut in uuts:
            init_dual_chirp(args, uut)
          
        if args.gps_sync > 1:
            ttime = time.time() + args.gps_sync
            for uut in uuts:
                uut.s2.trigger_at = ttime
            time.sleep(args.gps_sync+1)
        
        if not args.noverify:
            for uut in uuts:
                verify_chirp(uut, test)
                


def run_main():
    parser = argparse.ArgumentParser(description='radcelf-chirp-init')
    parser.add_argument('--test', default=1, type=int,
                        help="set number of tests to run")
    parser.add_argument('--debug', default=0, type=int, help="1: trace 2: step")
    parser.add_argument('--noverify', default=0, type=int, help="do not verify (could be waiting gps)")
    parser.add_argument('--noinitremapper', default=1, type=int, help="keep existing clock remapper ")
    parser.add_argument('--gps_sync', default=0, type=int, help="syncronize with GPSPPS >1: autotrigger at + gps_sync s")
    parser.add_argument('--legacy_radcelf_init', default=0, type=int, help="use old script in case all-python does not work")
    parser.add_argument('uuts', nargs='*', default=["localhost"], help="uut")
    args = parser.parse_args()
    if args.debug: 
        Debugger.enabled = args.debug
    run_test(args)

# execution starts here


if __name__ == '__main__':
    run_main()
