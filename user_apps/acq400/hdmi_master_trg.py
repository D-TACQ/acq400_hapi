#!/usr/bin/env python

import acq400_hapi
import argparse
import time

def trigger(args):
    uut = acq400_hapi.Acq400(args.uut[0]) 
    uut.s0.SIG_SYNC_BUS_OUT_TRG=1
    time.sleep(1)
    uut.s0.SIG_SYNC_BUS_OUT_TRG=0

def get_parser():
    parser = argparse.ArgumentParser(description='hdmi trigger')
    parser.add_argument('uut', type=str, nargs = 1, help="uut")
    return parser

if __name__ == '__main__':
    trigger(get_parser().parse_args())

