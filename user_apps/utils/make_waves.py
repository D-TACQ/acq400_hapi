#!/usr/bin/env python
'''
make_waves ... make a related set of waveforms, store as raw binary, one file per channel
Created on 8 Jun 2021

@author: pgm
'''

import numpy as np
import argparse
from asyncio.protocols import DatagramProtocol
import sys

import matplotlib.pyplot as plt


def ramp(args):    
    return np.linspace(-args.amp, args.amp, num=args.len)



def np_type(args):   
    np.int32 if args.res != 16 else np.int16
    
def make_waves(args, iarg):
    print("make_waves")
    ch0 = ramp(args)
    print("shape ch0 {}".format(ch0.shape))
    args.chx = np.zeros([args.len, args.nchan])
    for ch in range(0, args.nchan):
        offset = (ch - args.nchan/2)*args.offset_per_channel
        args.chx[:,ch] = ch0 + offset
        
        
def store_files(args, iarg):
    print("store_files")
    if args.root:
        for ch in range(0, args.nchan):
            offset = (ch - args.nchan/2)*args.offset_per_channel
            args.chx[:,ch].tofile("{}/ch{:02d}_{}_{}+{:.2}V.dat".
                             format(args.root, ch, args.len, args.amp, offset))

def scale_raw(args, iarg):
    scale = (1 << (args.res-1))/args.vmax
    args.raw = (args.chx * scale).astype(np_type(args))
    
    
def store_raw(args, iarg):    
    print("store_raw")
    args.raw.tofile("{}/myfile.raw".format(args.root))

def load_files(args, iarg):
    print("load_files @@todo")
        
def load_raw(args, iarg):
    print("load_raw")
    args.raw = np.fromfile("{}/myfile.raw".format(args.root), np_type(args)).reshape((-1,args.nchan))

def plot1(args, iarg):
    print("shape of plot data {}".format(args.raw.shape))
    plt.plot(args.raw)
    plt.show()
    
class ExitException(BaseException):
    pass




def load_uut(args, iarg):
    print("load_uut {}".format(" ".join(args.ops[iarg:])))
    print("exit")
    raise ExitException


def is_param(args, iarg):
    print("is_param")
    
OPS = { "generate": make_waves, 
       "store_files": store_files, "load_files": load_files, 
       "store_raw": store_raw, "load_raw": load_raw,
       "scale_raw": scale_raw,
       "plot1": plot1,
       "load_uut": load_uut, "UUT": is_param, "continuous": is_param, "autorearm": is_param }
        
def ui():
    parser = argparse.ArgumentParser(description='make_awg_data')
    parser.add_argument('--nchan',  default=16,     type=int,   help="number of channels in set")
    parser.add_argument('--len',    default=100000, type=int,   help="number of samples in set")
    parser.add_argument('--amp',    default=1.0,                help="amplitude in volts")
    parser.add_argument('--ncycles', default=8,     type=int,   help="number of waveform cycles in set")
    parser.add_argument('--offset_per_channel', default=0.0, type=float,     help="offset in volts *ch")
    parser.add_argument('--res',   default=16, type=int,        help="word size in bits")
    parser.add_argument('--vmax',   default=10.0, type=float,   help="full scale voltage (always symmetrical twos comp")
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

def run_main():
    args = ui()
    for iarg, op in enumerate(args.ops):
        try:
            OPS[op](args, iarg)
        except ExitException:
            print("quitting time")
            sys.exit(0)
        except Exception as e:
            print("rejected {} {}".format(op, e))
        

# execution starts here
if __name__ == '__main__':
    run_main()