#!/usr/bin/env python

'''
Created on 3 Nov 2020

@author: pgm

make_awg_data fname

example usage:
MAD32="./user_apps/utils/make_awg_data.py --nchan=32"
$MAD32 --len=16384 --amp=0.1 --offset_by_channel=0.1 --ncycles=8 32CH_0V1_16384_POFFSET_8CYCLES.dat
$MAD32 --len=16384 --amp=0.1 --offset_by_channel=0.1 --ncycles=128 32CH_0V1_16384_POFFSET_128CYCLES.dat
$MAD32 --len=16384 --amp=0.1 --offset_by_channel=0.1 --ncycles=1024 32CH_0V1_16384_POFFSET_1024CYCLES.dat
$MAD32 --len=16384 --amp=0.1 --offset_by_channel=0.1 --ncycles=64 32CH_0V1_16384_POFFSET_64CYCLES.dat
$MAD32 --len=8192 --amp=0.1 --offset_by_channel=0.1 --ncycles=64 32CH_0V1_8192_POFFSET_64CYCLES.dat

'''

import numpy as np
import argparse

def make_awg_data(args):
    x = np.linspace(0, args.ncycles*np.pi, args.len)
    y = args.amp * np.sin(x) D32
    volts = np.zeros([args.len, args.nchan])
    for ch in range(args.nchan):
        volts[:,ch] = np.add(y, ch*args.offset_by_channel)
    
    raw = (volts * 32767/10).astype(np.int16)
    raw.tofile(args.fname[0])
    
    
def run_main():
    parser = argparse.ArgumentParser(description='make_awg_data')
    parser.add_argument('--nchan',  default=16,     type=int,   help="number of channels in set")
    parser.add_argument('--len',    default=100000, type=int,   help="number of samples in set")
    parser.add_argument('--amp',    default=1.0,    type=float, help="amplitude in volts")
    parser.add_argument('--ncycles', default=8,     type=int,   help="number of waveform cycles in set")
    parser.add_argument('--offset_by_channel', default=0.0, type=float,     help="offset in volts *ch")
    parser.add_argument('fname', nargs=1)
    args = parser.parse_args()
    make_awg_data(args)

# execution starts here


if __name__ == '__main__':
    run_main()
