#!/usr/bin/env python
'''
pg_test : loads pg with STL and starts. remotable version of CARE/pg_test
Created on 17 Aug 2021

@author: pgm

usage: pg_trigger_tester.py : run wrt_txi in a steady loop, check each unit saw a WRTT0, and optionally check that PG sites also triggered.

'''
import acq400_hapi
import os
import argparse
import sys
import time

    
def get_args():
    parser = argparse.ArgumentParser(description='pg_test')
    parser.add_argument('--site', default='6', help="list of sites eg 5,6 to load")
    parser.add_argument('--interval', default=3, type=int, help="trigger interval in s" )
    parser.add_argument('--shots', default=10, type=int, help="number of shots")
    parser.add_argument('--pulse_count', default=0, type=int, help="count output pulses on AUX2/TRG.d0")
    parser.add_argument('uut', nargs='+', help="uuts")
    args = parser.parse_args()
    args.sites = [ int(x) for x in args.site.split(',') ]

    return args

def pg_test1(args, uut, site):
    site_svc = uut.svc['s{}'.format(site)]
    site_svc.GPG_ENABLE = 0
    if args.trg != 'NOTOUCH':
        site_svc.trg = args.trg
    if args.tscale:
        site_svc.gpg_timescaler = int(args.tscale)
    uut.load_dio482pg(site, args.STL[site], trace=args.stl_trace)
    site_svc.GPG_MODE = args.mode
    mode_rb = acq400_hapi.Acq400.pv(site_svc.GPG_MODE)
    if mode_rb != args.mode:
        print("WARNING: specified mode '{}' rejected, currently set '{}'".format(args.mode, mode_rb))
    site_svc.GPG_ENABLE = 1
    
    
#acq2106_345:0:SIG:TRG_S2:RESET
    
def pg_trigger_test_init(args, uuts):
    for u in uuts:
        u.cC.WR_WRTT0_RESET = '1'
        for site in args.sites:
            u.s0.set_knob("SIG_TRG_S{}_RESET".format(site), '1')
            u.modules[site].bypass_trg_debounce = 1
        if args.pulse_count:
            u.s0.SIG_EVT_EXT_RESET = '1'
            
    
def get_counts(args, u):
    counts = [ acq400_hapi.Acq400.intpv(u.cC.WR_WRTT0_COUNT), ]
    counts.append([ acq400_hapi.Acq400.intpv(u.s0.get_knob("SIG_TRG_S{}_COUNT".format(s))) for s in (args.sites)])
    return counts  
def pg_trigger_test1(args, uuts):
    print("trigger!")
    uuts[0].cC.wrtd_txi = 1
    time.sleep(args.interval)
    counts = []
    for u in uuts:
        if args.pulse_count:
            npc = acq400_hapi.Acq400.intpv(u.s0.SIG_EVT_EXT_COUNT)
            pc = "pulse count: {} pc/wrtt {}".format(npc, npc/acq400_hapi.Acq400.intpv(u.cC.WR_WRTT0_COUNT))
        else:
            pc = ""
        print("{} wrtt, pgidx {} {}".format(u.uut, get_counts(args, u), pc))
        
        
def pg_trigger_test(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uut ]
    
    pg_trigger_test_init(args, uuts)
    
    for shot in range(0, args.shots):
        pg_trigger_test1(args, uuts)
    

def main():
    pg_trigger_test(get_args())

if __name__ == '__main__':
    main()
