#!/usr/bin/env python

""" 
acq2106_set_sync_role master [slave1 ... slaveN]
"""

import argparse
import acq400_hapi
import time

def set_mb_clk(uut, clkdef):
    if (len(clkdef) == 3):
        (src, hz, fin) = clkdef
        uut.set_mb_clk(hz=hz, src=src, fin=fin)
    else:
        (src, hz) = clkdef
        uut.set_mb_clk(hz=hz, src=src)


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
            uut.set_sync_routing_master( trg_dx="d1" if mtrg=="soft" else "d0", clk_dx="d2")

            uut.set_master_trg(mtrg, edge, enabled = True if mtrg=="soft" else False)
            set_mb_clk(uut, parser.master_clk.split(','))            
            role = "slave"
            trg = "1,%d,%d" % (1 if mtrg=="soft" else 0, rf(edge))
            clkdiv = parser.clkdiv
        else:
            trg = "1,%d,%d" % (0, rf(parser.trg_edge))
            clkdiv = 1
            uut.set_sync_routing_slave()

        uut.s0.SIG_TRG_EXT_RESET = '1'  # self-clears   

        uut.s1.trg = trg
        uut.s1.clk = '1,1,1'
        uut.s1.clkdiv = clkdiv
        uut.s1.CLKDIV = clkdiv

    if parser.test:
        run_link_test(parser, uuts[0], uuts[1])

    if not parser.master_trg.startswith("soft"):
        raw_input("say when")
        uuts[0].set_master_trg(mtrg, edge, enabled=True)       


# execution starts here

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="acq2106_set_sync_role")
    parser.add_argument("--master_clk", default="zclk,2000000", help="master_clk role alt fp,sysclk,sampleclk")
    parser.add_argument("--master_trg", default="soft,rising", help="master_trg src alt: fp")    
    parser.add_argument("--clkdiv", default="1", help="clock divider, each module")
    parser.add_argument("--test", default=0, help="test link")
    parser.add_argument("--trace", default=0, help="set command tracing")
    parser.add_argument("uuts", nargs='+', help="uuts m1 [s1 s2 ...]")
    run_main(parser.parse_args())


