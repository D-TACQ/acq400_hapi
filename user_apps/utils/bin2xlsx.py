#!/usr/bin/env python

"""
bin2xlsx
input raw binary, output xlsx

usage: bin2xlsx.py [-h] [--nchan NCHAN] [--word WORD] [--outroot OUTROOT]
                  [--out OUT] [--paste PASTE]
                  binfiles [binfiles ...]

bin2xlsx

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

import xlsxwriter
import argparse
import numpy as np
import os
#from slip._wrappers._glib import _self

def get_word_type(wtype):
    if wtype == 'int16':
        return np.int16
    elif wtype == 'int32':
        return np.int32
    else:
        print("ERROR, undefined word type {}".format(wtype))
        exit(1)

def xlsx_name(args, binfile):
    if len(args.out) > 0:
        basename = args.out
    else:
        basename, extn = os.path.splitext(binfile)

    return "{}{}{}.xlsx".format(args.outroot, os.sep if len(args.outroot)>0 else '', basename)
   
def bin2xlsx_onesource_manychan(args):
    for src in args.binfiles:
        raw = np.fromfile(src, args.wtype)
        nrows = len(raw)//args.nchan
        chx = np.reshape(raw[:nrows*args.nchan], (nrows, args.nchan))
        
        workbook = xlsxwriter.Workbook(xlsx_name(args, src))
        worksheet = workbook.add_worksheet()
              
        for row in range(0, nrows):
            for col in range(0, args.nchan):
               worksheet.write(row, col, chx[row, col])
               
        workbook.close()
                
                
def bin2xlsx_many_onechan_sources(args):
    chx = list()
    for binf in args.binfiles:
        chx.append(np.fromfile(binf, args.wtype))
    lens = [ len(u) for u in chx ]
    nrows = lens[0]
    chxx = np.vstack(chx)
    workbook = xlsxwriter.Workbook(xlsx_name(args, args.binfiles[0]))
    worksheet = workbook.add_worksheet()
    
    for row in range(0, nrows):
        for col in range(0, args.nchan):
            worksheet.write(row, col, chx[row, col])
               
    workbook.close()
            
def bin2xlsx(args):
    args.wtype = get_word_type(args.word)
    if args.paste:
        bin2xlsx_many_onechan_sources(args)
    else:
        bin2xlsx_onesource_manychan(args)
        
def run_main():
    parser = argparse.ArgumentParser(description='bin2xlsx')
    parser.add_argument('--nchan', default=1, type=int, help="number of channels")
    parser.add_argument('--word', default='int16', help="int16|int32")
    parser.add_argument('--outroot', default='', help="output root directory")
    parser.add_argument('--out', default='', help="explicit output name")
    parser.add_argument('--paste', default=0, type=int, help="1: paste multiple files * 1 chan")
    parser.add_argument('binfiles', nargs='+', help="file[s] to convert")
    bin2xlsx(parser.parse_args())
     
    
    
# execution starts here

if __name__ == '__main__':
    run_main()
