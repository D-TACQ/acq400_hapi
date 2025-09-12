#!/usr/bin/env python

'''
make_awg_data_id_set fname

Makes a series of waveforms, each with one of the channels as an "ID"

regular: sin at +1V
id     : cos at -1V

Created on 3 Nov 2020

@author: pgm

'''

import numpy as np
import argparse

def make_awg_data(args):
    if args.data32 == 1:
        args.dtype = np.int32
        rmax = 2**31
    else:
        args.dtype = np.int16
        rmax = 2**15

    x = np.linspace(0, 8*np.pi, args.len)
    y = args.amp * np.sin(x) 
    volts = np.zeros([args.len, args.nchan])
    for ch in range(args.nchan):
        volts[:,ch] = np.add(y, args.offset + ch*args.offset_by_channel)
    
    basev = (volts * rmax/10).astype(args.dtype)
    
    cos = args.amp * np.sin(x+np.pi/2)
    cosv = (np.add(cos, -args.offset) * rmax/10).astype(args.dtype)
    return(cosv, basev)
    
def next(args, ch):
    if ch+1 < args.nchan:
        return ch+1
    else:
        return ch
    
def make_id_set(args): 
    if args.duphalf == 0:
        maxch = args.nchan
        patoff = (0,)
    else:
        maxch = args.nchan//2
        patoff = (0, maxch)

    if args.max_seg is not None and args.max_seg < maxch:
        maxch = args.max_seg
      
    cosv, basev = make_awg_data(args)

    for ch in range(0, maxch):
        chv = basev
        for chid in [ x+ch for x in patoff ]:
            chv[:,chid] = np.zeros([args.len,])
            id_len = args.len*((ch+1)%8)//8
            chv[:id_len,chid] = cosv[:id_len]

        data32id = ""
        if args.data32 == 1:
            data32id = f"d32"
        fn = f"{args.fname[0]}-{args.nchan}-{args.len}{data32id}-{ch+1:03d}.dat"
        print(fn)
        chv.tofile(fn)
    
    
    
    
def get_parser():
    parser = argparse.ArgumentParser(description='make_awg_data')
    parser.add_argument('--nchan',  default=16,     type=int,   help="number of channels in set")
    parser.add_argument('--len',    default=100000, type=int,   help="number of samples in set")
    parser.add_argument('--amp',    default=0.5, type=float,    help="amplitude in volts")
    parser.add_argument('--ncycles', default=8,     type=int,   help="number of waveform cycles in set")
    parser.add_argument('--offset_by_channel', default=0.0, type=float,     help="offset in volts *ch")
    parser.add_argument('--offset', default=1.0, type=float,     help="global offset in volts ")
    parser.add_argument('--offset_c1', default=1.0, type=float,  help="ch+1 output with this offset")
    parser.add_argument('--duphalf', default=0, type=int, help="repeat pattern from half channels - good for 2 sites compare")
    parser.add_argument('--max_seg', default=None, type=int, help="optionally limit the number of files generated. Better for LARGE data")
    parser.add_argument('--data32', default=0, type=int, help="set data32 mode")
    parser.add_argument('fname', nargs=1, help="filename root")
    return parser

# execution starts here


if __name__ == '__main__':
    make_id_set(get_parser().parse_args())
