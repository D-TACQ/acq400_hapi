#!/usr/bin/env python

""" creates a CLK + TRG daisy chain using the SYNC (HDMI) ports
    make_clktrg_chain UUTM UUTS1 [UUTS2..]
    where UUTM is the ip-address or host name of first uut
    trigger on UUTM triggers all other slaves in the chain
"""

import sys
import acq400_hapi
import argparse


def make_chain(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    uutm = uuts[0]
    UUTS = uuts[1:]
    
    uutm.set_sync_routing_master( \
        trg_dx = "d0" if args.trg=="fp" else "d1", \
        clk_dx = "d0" if args.clk==0 else "d1" )
    if args.clk > 0:
        uutm.set_mb_clk(args.clk)
        
    for uut in UUTS:
        uut.set_sync_routing_slave()
        

def run_main():
    parser = argparse.ArgumentParser(description='make_clktrg_chain')    
    parser.add_argument('--trg', default='fp', type=str, help="trigger fp|soft")
    parser.add_argument('--clk', default='0', type=int, help='clk 0=fp | intclk in Hz')
    parser.add_argument('uuts', nargs='+', help="uut : UUTM, UUTS ...")
    make_chain(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
