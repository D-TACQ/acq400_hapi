#!/usr/bin/env python

""" 
acq2106_set_sync_role master [slave1 ... slaveN]

usage: acq2106_set_sync_role.py [-h] [--master_clk MASTER_CLK]
                                [--master_trg MASTER_TRG] [--clkdiv CLKDIV]
                                [--test TEST] [--trace TRACE]
                                uuts [uuts ...]

acq2106_set_sync_role

positional arguments:
  uuts                  uuts m1 [s1 s2 ...]

optional arguments:
  -h, --help            show this help message and exit
  --master_clk MASTER_CLK
                        master_clk role alt fp,sysclk,sampleclk
  --master_trg MASTER_TRG
                        master_trg src alt: fp
  --clkdiv CLKDIV       clock divider, each module
  --test TEST           test link
  --trace TRACE         set command tracing
"""

import argparse
import acq400_hapi
import time
from future import builtins
from builtins import input

def set_mb_clk(uut, clkdef):
    fmt = acq400_hapi.intSI_cvt
    if (len(clkdef) == 3):
        (src, hz, fin) = clkdef
        uut.set_mb_clk(hz=fmt(hz), src=src, fin=fmt(fin))
    else:
        (src, hz) = clkdef
        uut.set_mb_clk(hz=fmt(hz), src=src)


def rf(edge):
    return 1 if edge == "rising" else 0

def run_link_test(parser, uutm, uuts):
    print("Cable test:")
    uutm.s0.SIG_SYNC_BUS_OUT_CABLE_DET
    uutm.s0.SIG_CLK_MB_FREQ
    uuts.s0.SIG_CLK_MB_FREQ
    if parser.master_trg.startswith("soft"):
        print("Soft Trigger test:")
        uuts.s0.SIG_TRG_EXT_COUNT
        uutm.s0.soft_trigger
        time.sleep(1)
        uuts.s0.SIG_TRG_EXT_COUNT

def sync_trg_to_clk(uut, value = '1'):
    try:
        uut.s1.sync_trg_to_clk = value
    except AttributeError:
        print("{} failed to set sync_trg_to_clk {} .. old firmware".format("NOTE" if value == '1' else "ERROR", value))

def run_main(parser):
    uuts = [ acq400_hapi.Acq2106(addr) for addr in parser.uuts ]      
    role = "master"

    for uut in uuts:
        uut.s0.trace = parser.trace
        uut.s1.trace = parser.trace

        if role == "master":                        
            # ensure there are two values to unpack, provide a default for the 2nd value..
            mtrg, edge = (parser.master_trg.split(',') + [ "rising" ])[:2]             
            parser.trg_edge = edge                     
            set_mb_clk(uut, parser.master_clk.split(','))
            # use Si5326 direct output where possible (almost always!)
            _clk_dx = "d2" if uut.s1.CLKDIV != 'CLKDIV 1' else "d1"
            uut.set_sync_routing_master( trg_dx="d2", clk_dx=_clk_dx)

            uut.set_master_trg(mtrg, edge)
            role = "slave"
            trg = "1,%d,%d" % (1 if mtrg=="soft" else 0, rf(edge))
            clkdiv = parser.clkdiv
            sync_trg_to_clk(uut)
        else:
            trg = "1,%d,%d" % (0, rf(parser.trg_edge))
            clkdiv = 1
            uut.set_sync_routing_slave()
            uut.s1.CLKDIV = clkdiv
            sync_trg_to_clk(uut, parser.slave_sync_trg_to_clk)

        uut.s0.SIG_TRG_EXT_RESET = '1'  # self-clears. clear trigger count for easy ref 

        uut.s1.trg = trg
        uut.s1.clk = '1,1,1'

    if parser.test:
        run_link_test(parser, uuts[0], uuts[1])

    if not parser.master_trg.startswith("soft"):
        input("say when")
        uuts[0].set_master_trg(mtrg, edge, enabled=True)       


# execution starts here

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="acq2106_set_sync_role")
    parser.add_argument("--master_clk", default="zclk,2000000", help="master_clk role alt fp,sampleclk[,sysclk]")
    parser.add_argument("--master_trg", default="soft,rising", help="master_trg src alt: fp")    
    parser.add_argument("--clkdiv", default="1", help="clock divider, each module")
    parser.add_argument("--test", default=0, help="test link")
    parser.add_argument("--trace", default=0, help="set command tracing")
    parser.add_argument("--slave_sync_trg_to_clk", default='0', help="0: do NOT retime the trg on the slave")
    parser.add_argument("uuts", nargs='+', help="uuts m1 [s1 s2 ...]")
    run_main(parser.parse_args())


