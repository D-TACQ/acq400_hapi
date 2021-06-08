#!/usr/bin/env python
'''
make_waves ... make a related set of waveforms, store as raw binary, one file per channel
Created on 8 Jun 2021

@author: pgm
'''

import numpy as np
import argparse

def ui():
    parser = argparse.ArgumentParser(description='make_awg_data')
    parser.add_argument('--nchan',  default=16,     type=int,   help="number of channels in set")
    parser.add_argument('--len',    default=100000, type=int,   help="number of samples in set")
    parser.add_argument('--amp',    default=1.0,                help="amplitude in volts")
    parser.add_argument('--ncycles', default=8,     type=int,   help="number of waveform cycles in set")
    parser.add_argument('--offset_by_channel', default=0.0, type=float,     help="offset in volts *ch")
    parser.add_argument('--res',   default=16, type=int,   help="word size in bits")
    parser.add_argument('--fxn', default="ramp", help="function to execute")
    parser.add_argument('--root', default='DATA',     help="offset in volts *ch")
    parser.add_argument('--merge', default=1,  help="merge data into single binary")
    parser.add_argument('--expand_to', default=4*0x400000, help="expand to fit binary block size")
    parser.add_argument('--uut', default=None, help="load to uut uut[A,C] A=1: AUTOREARM, C=1: CONTINUOUS")    
    return parser.parse_args()
    
    
def make_waves(args):
    pass

def run_main():
    args = ui()
    make_waves(args)

# execution starts here
if __name__ == '__main__':
    run_main()