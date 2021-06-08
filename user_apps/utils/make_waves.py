#!/usr/bin/env python
'''
make_waves ... make a related set of waveforms, store as raw binary, one file per channel
Created on 8 Jun 2021

@author: pgm
'''

import numpy as np
import argparse
from asyncio.protocols import DatagramProtocol


def ramp(args):    
    return np.linspace(-args.amp, args.amp, num=args.len)

OPS = ( "generate", "store_files", "load_files", "load_uut", "UUT", "continuous", "autorearm" )
        
def ui():
    parser = argparse.ArgumentParser(description='make_awg_data')
    parser.add_argument('--nchan',  default=16,     type=int,   help="number of channels in set")
    parser.add_argument('--len',    default=100000, type=int,   help="number of samples in set")
    parser.add_argument('--amp',    default=1.0,                help="amplitude in volts")
    parser.add_argument('--ncycles', default=8,     type=int,   help="number of waveform cycles in set")
    parser.add_argument('--offset_per_channel', default=0.0, type=float,     help="offset in volts *ch")
    parser.add_argument('--res',   default=16, type=int,        help="word size in bits")
    parser.add_argument('--fxn', default="ramp",                help="function to execute")
    parser.add_argument('--root', default='DATA',               help="offset in volts *ch")
    parser.add_argument('--merge', default=1,                   help="merge data into single binary")
    parser.add_argument('--expand_to', default=4*0x400000,      help="expand to fit binary block size")
    parser.add_argument('ops', nargs='+', help="operations: one or more of "+" ".join(OPS)+" # for UUT, substitute UUT name")
    
    args = parser.parse_args()
    if args.fxn == 'ramp':
        args.fn = eval('ramp')
    else:
        print("ERROR: fxn {} not available".format(args.fxn))
    return args

    

def make_waves(args):
    ch0 = ramp(args)
    chx = np.zeros([args.len, args.nchan])
    for ch in range(0, args.nchan):
        offset = (ch - args.nchan/2)*args.offset_per_channel
        chx[:,ch] = ch0 + offset
        if args.root:
            chx[:,ch].tofile("{}/ch{:02d}_{}_{}+{}V.dat".
                             format(args.root, ch, args.len, args.amp, offset))
        
def store_files(args):
    pass
    
        
    

def run_main():
    args = ui()
    for op in args.ops:
        if op == "generate":
            make_waves(args)
        elif op == "store_files":
            store_files(args)
        

# execution starts here
if __name__ == '__main__':
    run_main()