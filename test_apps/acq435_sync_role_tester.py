#!/usr/bin/env python3
'''
Created on 1 Sep 2020

@author: pgm
'''

import argparse
import acq400_hapi
import time

def get_args():
    parser = argparse.ArgumentParser(description='Test sync_role')
    parser.add_argument('--ntests', default=1, type=int, help="number of tests to run")
    parser.add_argument('uuts', nargs=1, help="uut")
    return parser.parse_args()


def pf(args, f1, f2):
    err = abs(f1 - f2)
    args.fail = err/f1 > 0.01
    return "FAIL" if args.fail else "PASS"


def get_fs_actual(uut):
    return round(float(uut.s0.SIG_SYN_S1_FREQ.split(" ")[1]))

def is_within_limits(f1, f2):
    err = abs(f1 - f2)
    return err/f1 < 0.01

def run_test(args, uut, tn):
    print("Test {} Start".format(tn))
    
    
    if uut.s0.CONTINUOUS.split(" ")[1] != "stop":
        uut.s0.CONTINUOUS = 0
        time.sleep(2)
    
    args.fail = 0
    
    for fs in ( 128000, 64000, 48000, 24000, 12000, 6000, 4000):
        for trg_dx in ( 'd0', 'd1'):
            uut.s0.sync_role = 'master {} TRG:DX={}'.format(fs, trg_dx)
            time.sleep(5)
            fs_set = uut.s1.ACQ43X_SAMPLE_RATE
            adc_clk = round(float(uut.s0.SIG_CLK_S1_FREQ.split(" ")[1]))
            hr_mode = int(uut.s1.hi_res_mode)
            adc_div = 512 if hr_mode else 256
            fs_calc = round(adc_clk/adc_div)
            trg_dx_actual = uut.s1.TRG_DX.split(" ")[1]
            print("set {} adc_clk {} adc_div {} calc Fs {} Fs status:{} {} {}".
                  format(fs, adc_clk, adc_div, fs_calc, pf(args, fs, fs_calc), trg_dx, trg_dx_actual))
            print("enable capture and run 5s")
            uut.s0.CONTINUOUS = 1
            
            for retry in range(0, 20):
                fs_actual = get_fs_actual(uut)
                if is_within_limits(fs, fs_actual):
                    break
                else:
                    time.sleep(1)
                
            state = int(uut.s0.state.split(" ")[0])
            print("set {} actual {} clock status {} capture state {} capture status {}".
                  format(fs, fs_actual, pf(args, fs, fs_actual), state, 
                         "PASS" if trg_dx=='d0' and state >=1 or trg_dx=='d1' and state>1 else "FAIL"))
            if args.fail:
                print("FAIL FAIL FAIL")
                exit(1)
            uut.s0.CONTINUOUS = 0
            

def run_test_top(args):
    
    uut = acq400_hapi.Acq400(args.uuts[0])
    
    for tn in range(0, args.ntests):
        run_test(args, uut, tn)
    
    
def main():
    args = get_args()
    run_test_top(args)
    
if __name__ == '__main__':
    main()