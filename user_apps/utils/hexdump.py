#!/usr/bin/env python

"""
bin2csv
input raw binary, output csv

usage: bin2csv.py [-h] [--nchan NCHAN] [--word WORD] [--outroot OUTROOT]
                  [--out OUT] [--paste PASTE]
                  binfiles [binfiles ...]

bin2csv

positional arguments:
  binfiles           file[s] to convert

optional arguments:
  -h, --help         show this help message and exit
  --nchan NCHAN      number of channels
  --word WORD        int16|int32
  --outroot OUTROOT  output root directory
  --out OUT          explicit output name
  --paste PASTE      1: paste multiple files * 1 chan
"""

import csv
import argparse
import numpy as np
import os

def get_word_type(args, wtype):
    if wtype == 'int16':
        args.hexfmt = '%6d'
        args.wtype = np.int16
    elif wtype == 'int32':
        args.hexfmt = '%12d'
        args.wtype = np.int32
    elif wtype == 'uint16':
        args.hexfmt = '%04x,'
        args.wtype = np.uint16
    elif wtype == 'uint32':
        args.hexfmt = '%08x,'
        args.wtype = np.uint32
    else:
        print("ERROR, undefined word type {}".format(wtype))
        exit(1)

def hexdump2d(args, chx, nrows):
    try:
        for row in range(nrows):
            for col in range(args.nchan):
                print(args.hexfmt % chx[row][col], end = '\n' if col == args.nchan-1 else '')
    except BrokenPipeError:
        pass

                
def hexdump_onesource_manychan(args):
    for src in args.binfiles:
        raw = np.fromfile(src, args.wtype)
        nrows = len(raw)//args.nchan
        chx = np.reshape(raw, (nrows, args.nchan))
        hexdump2d(args, chx, nrows)        
                
def hexdump_many_onechan_sources(args):
    chx = list()
    for binf in args.binfiles:
        chx.append(np.fromfile(binf, args.wtype))
    lens = [ len(u) for u in chx ]
    nrows = lens[0]
    chxx = np.vstack(chx)   
    
    hexdump2d(args, np.vstack[chx], nrows)

            
def hexdump(args):
    get_word_type(args, args.word)

    if args.paste:
        hexdump_many_onechan_sources(args)
    else:
        hexdump_onesource_manychan(args)
        
def run_main():
    parser = argparse.ArgumentParser(description='bin2csv')
    parser.add_argument('--nchan', default=1, type=int, help="number of channels")
    parser.add_argument('--word', default='int16', help="int16|int32,uint16,uint32")
    parser.add_argument('--outroot', default='', help="output root directory")
    parser.add_argument('--out', default='', help="explicit output name")
    parser.add_argument('--paste', default=0, type=int, help="1: paste multiple files * 1 chan")
    parser.add_argument('binfiles', nargs='+', help="file[s] to convert")
    hexdump(parser.parse_args())
     
    
    
# execution starts here

if __name__ == '__main__':
    run_main()
