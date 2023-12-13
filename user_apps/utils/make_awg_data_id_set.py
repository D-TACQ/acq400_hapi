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
    x = np.linspace(0, 8*np.pi, args.len)
    y = args.amp * np.sin(x) 
    volts = np.zeros([args.len, args.nchan])
    for ch in range(args.nchan):
        volts[:,ch] = np.add(y, args.offset + ch*args.offset_by_channel)
    
    basev = (volts * 32767/10).astype(np.int16)
    
    cos = args.amp * np.sin(x+np.pi/2)
    cosv = (np.add(cos, -args.offset) * 32767/10).astype(np.int16)
    return(cosv, basev)
    
def next(args, ch):
    if ch+1 < args.nchan:
        return ch+1
    else:
        return ch
    
def make_id_set(args): 
    cosv, basev = make_awg_data(args)
    
    for ch in range(0, args.nchan):
        chv = basev
        chv[:,ch] = np.zeros([args.len,])
        id_len = args.len*((ch+1)%8)//8
        chv[:id_len,ch] = cosv[:id_len]        
        fn = f"{args.fname[0]}-{args.nchan}-{args.len}-{ch+1}.dat"
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
    parser.add_argument('fname', nargs=1, help="filename root")
    return parser

# execution starts here


if __name__ == '__main__':
    make_id_set(get_parser().parse_args())
