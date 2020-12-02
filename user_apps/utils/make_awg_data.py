#!/usr/bin/env python

'''
Created on 3 Nov 2020

@author: pgm

make_awg_data fname

'''

import numpy as np
import argparse

def make_awg_data(args):
    x = np.linspace(0, 8*np.pi, args.len)
    y = args.amp * np.sin(x) 
    volts = np.zeros([args.len, args.nchan])
    for ch in range(args.nchan):
        volts[:,ch] = np.add(y, ch*args.offset_by_channel)
    
    raw = (volts * 32767/10).astype(np.int16)
    raw.tofile(args.fname[0])
    
    
def run_main():
    parser = argparse.ArgumentParser(description='make_awg_data')
    parser.add_argument('--nchan',  default=16,     type=int,   help="number of channels in set")
    parser.add_argument('--len',    default=100000, type=int,   help="number of samples in set")
    parser.add_argument('--amp',    default=1.0,                help="amplitude in volts")
    parser.add_argument('--ncycles', default=8,     type=int,   help="number of waveform cycles in set")
    parser.add_argument('--offset_by_channel', default=0.0, type=float,     help="offset in volts *ch")
    parser.add_argument('fname', nargs=1)
    args = parser.parse_args()
    make_awg_data(args)

# execution starts here


if __name__ == '__main__':
    run_main()