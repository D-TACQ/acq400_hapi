#!/usr/bin/env python3
'''
slowmon.py: receive and process slowmon data
'''

import acq400_hapi
import numpy as np
import os
import time
import argparse
import sys
import shutil


def run_stream(args):
    return
    
def run_main():
    parser = argparse.ArgumentParser(description='acq400 slowmon')
    parser.add_argument('--show_raw', default=None, type=str, help="show raw data, 'd'=decimal, 'h'=hex")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('uuts', nargs=1, help="uuts")
    args = parser.parse_args()
    
    uut = acq400_hapi.factory(args.uuts[0])
    args.ssb = int(uut.s0.ssb)
    args.data32 = int(uut.s0.data32)
    args.nspad = int(uut.s0.spad.split(',')[1])
    args.nchan = (args.ssb - 4*args.nspad)//(4 if args.data32 else 2)
    
    print("ssb: {} nchan: {}*{} nspad:{}".format(args.ssb, args.nchan, 4 if args.data32 else 2, args.nspad))
    run_stream(args)


if __name__ == '__main__':
    run_main()