#!/usr/bin/env python
'''
wrtd_trigger_tester : exercises wrtd_txi and wrtd_txq on WRTT0, WRTT1, could extent to PG's..
Created on 17 Aug 2021

@author: pgm

usage: pg_trigger_txq_tester.py : how close can we reliably separate two txq messages?

'''
import acq400_hapi
import os
import argparse
import sys
import time

    
def get_args():
    parser = argparse.ArgumentParser(description='wrtd_trigger_tester')    
    parser.add_argument('--interval', default=0.1, type=float, help="trigger interval in s" )
    parser.add_argument('--shots', default=10, type=int, help="number of shots") 
    parser.add_argument('--trgtype', default='wrtd_txi', help="trigger type [wrtd_txi] or wrtd_txq")
    parser.add_argument('--doubletap', default=None, help="double tap id")
    parser.add_argument('uut', nargs='+', help="uuts")    
    return parser.parse_args()

   
#acq2106_345:0:SIG:TRG_S2:RESET
    
def pg_trigger_test_init(args, uuts):
    for u in uuts:
        u.cC.WR_WRTT0_RESET = '1'
        u.cC.WR_WRTT1_RESET = '1'
        u.s0.SIG_SRC_TRG_0 = 'WRTT0'    # default on WR system
        u.s0.SIG_SRC_TRG_1 = 'WRTT1'    # repalce STRG.
    
 
def pg_trigger_test1(args, uuts):
    print("trigger!")
    uuts[0].cC.set_knob(args.trgtype, "--tx_mask=1 1")
    time.sleep(args.interval)
    uuts[0].cC.set_knob(args.trgtype, "--tx_mask=2 1")   
    
def pg_trigger_test_double_tap(args, uuts):
    print("doubletap!")
#    uuts[0].cC.wrtd_txq = args.doubletap
    uuts[0].cC.set_knob(args.trgtype, args.doubletap)
    time.sleep(args.interval)   
 
        
        
def pg_trigger_test(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uut ]

    the_test = pg_trigger_test1 
    
    if args.doubletap:
        the_test = pg_trigger_test_double_tap
        for u in uuts:
            if u.cC.WRTD_RX_DOUBLETAP != args.doubletap:
                print("uut:{} setting WRTD_RX_DOUBLETAP:{}".format(u.uut, args.doubletap))
                u.cC.WRTD_RX_DOUBLETAP = args.doubletap
                u.cC.wrtd_commit_rx = 1
    
    pg_trigger_test_init(args, uuts)
    
    for shot in range(0, args.shots):
        the_test(args, uuts)
 
    time.sleep(2)                   # let the counters ketchup
    for u in uuts:
        print("{} {}".format(acq400_hapi.Acq400.intpv(u.cC.WR_WRTT0_COUNT), acq400_hapi.Acq400.intpv(u.cC.WR_WRTT1_COUNT)))   

def main():
    pg_trigger_test(get_args())

if __name__ == '__main__':
    main()
