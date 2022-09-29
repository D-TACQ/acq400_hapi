#!/usr/bin/env python
'''
wrtd_trigger_tester : exercises wrtd_txa on WRTT0
Created on 17 Aug 2021

@author: pgm

usage: pg_trigger_txq_tester.py : how close can we reliably separate two txq messages?

'''
import acq400_hapi
import os
import argparse
import sys
import time

   
TICKS_PER_SECOND = 40000000

def get_args():
    parser = argparse.ArgumentParser(description='wrtd_trigger_tester')
    parser.add_argument('--wrtt0_trg_loopback', default=0, type=int, help="loopback WRTT0 out (AUX2) to TRG input and record latch time")
    parser.add_argument('--txa', default=0, type=int, help="send txa message")   
    parser.add_argument('--hdmi', default=0, type=int, help="1: connect signals via HDMI")
    parser.add_argument('--shots', default=10, type=int, help="number of shots") 
    parser.add_argument('uut', nargs='+', help="uuts")    
    return parser.parse_args()

   
#acq2106_345:0:SIG:TRG_S2:RESET
    
def trigger_test_init(args, uuts):
    for u in uuts:
        u.cC.WR_WRTT0_RESET = '1'
        u.cC.WR_WRTT1_RESET = '1'
        u.s0.SIG_SRC_TRG_0 = 'WRTT0'    # default on WR system
        u.s0.SIG_SRC_TRG_1 = 'WRTT1'    # replace STRG.
        if args.wrtt0_trg_loopback != 0:
            if args.hdmi != 0:
                print("connect SYNC_OUT on BOX1 to SYNC_IN on BOX2 and vice-versa")
                u.s0.SIG_SYNC_OUT_TRG = 'TRG'
                u.s0.SIG_SYNC_OUT_TRG_DX = 'd0'
                u.s0.SIG_FP_GPIO = 'INPUT'
            else:
                print("connect FP AUX2 to TRG")
                u.s0.SIG_SYNC_OUT_TRG = 'DO'
                u.s0.SIG_FP_GPIO = 'EVT0'

            u.s0.WR_TRG_DX = 'HDMI' if args.hdmi != 0 else 'FPTRG'
            u.s0.WR_TRG_SENSE = 'rising'


        
def trigger_test(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uut ]
    
    trigger_test_init(args, uuts)

    count0 = [ acq400_hapi.intpv(u.cC.WR_WRTT0_COUNT) for u in uuts ]
    
    
    for shot in range(0, args.shots):
        if args.txa != 0:
            uuts[0].cC.wrtd_txa = '--at +1 1'
        else:
            uuts[0].cC.wrtd_txi = '1'
         
        count01 = [ count0[ii]+1 for ii in range(0, len(uuts))]
        pollcount = 0
        
        while True:   
            count1 = [ acq400_hapi.intpv(u.cC.WR_WRTT0_COUNT) for u in uuts ]

            pollcount += 1
            if count1 == count01:
                trg = [ [ int(x) for x in u.s0.wr_tai_trg.split(' ')[1:]] for u in uuts ]
                for tv in trg[1:]:
                    if trg[0] != tv:
                        print("ERROR: mismatch trigger {}".format(trg))
                        sys.exit(1)
                if args.wrtt0_trg_loopback != 0:
                    tai_ts = [ [ int(x) for x in u.s0.wr_tai_stamp.split(' ')[1:] ] for u in uuts ]
                    tai_tss = [ tai_ts[ii][0]*TICKS_PER_SECOND + tai_ts[ii][1] for ii in range(len(uuts))]
                    tl0 = trg[0][0]*TICKS_PER_SECOND + trg[0][1]
                    tl_delta = [ tai_tss[ii]-tl0 for ii in range(len(uuts))]

                    print("{}: in {} {} {} {} {} {}".format("PASS" if max([abs(x) for x in tl_delta]) < 20 else "FAIL", 
                            pollcount, count1, trg, tai_ts, trg[0][1], tl_delta))
                else:
                    print("PASS: in {} {} {}".format(pollcount, count1, trg))
                break
            else:                
                if pollcount > 10:
                    print("ERROR {} -> {}".format(count0, count1))
                    sys.exit(1)
                else:               
                    time.sleep(1)
                    
        count0 = count1

def main():
    trigger_test(get_args())

if __name__ == '__main__':
    main()
