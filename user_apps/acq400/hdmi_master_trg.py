#!/usr/bin/env python

import acq400_hapi
import argparse
import time

def trigger(args):
    uut = acq400_hapi.Acq400(args.uut[0]) 
    uut.s0.SIG_SYNC_BUS_OUT_TRG=1
    time.sleep(1);
    uut.s0.SIG_SYNC_BUS_OUT_TRG=0

def run_main():
    parser = argparse.ArgumentParser(description='acq400 hdmi trigger')
    parser.add_argument('uut', type=str, nargs = 1, help="uut")
    trigger(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()


