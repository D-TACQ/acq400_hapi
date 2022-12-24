#!/usr/bin/env python3
'''
slowmon.py: receive and process slowmon data

examples:
[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --show_raw=d --pchan=8 acq2106_178 | head
0 [ 000089, -00016, 000003, -00059, -00115, -00109, -00147, 000005 ] [ 1891931137,          0, 1891931137,         83 ]
1 [ 000083, -00018, 000005, -00061, -00116, -00112, -00143, 000010 ] [ 1891931138,          0,          1,         83 ]
2 [ 000090, -00012, 000010, -00053, -00111, -00110, -00141, 000012 ] [ 1891931139,          0,          1,         83 ]

[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --show_raw=h --pchan=8 acq2106_178 | head
0 [ 0052, ffed, 0004, ffc6, ff8a, ff8f, ff6e, 0009 ] [ 723a5001, 00000000, 723a5001, 00000030 ]
1 [ 005b, fff1, 0007, ffca, ff8c, ff94, ff75, 000a ] [ 723a5002, 00000000, 00000001, 00000030 ]
2 [ 0058, fff3, 0005, ffc8, ff8f, ff94, ff71, 0009 ] [ 723a5003, 00000000, 00000001, 00000030 ]
3 [ 0054, ffef, 0001, ffc3, ff8a, ff92, ff6f, 0006 ] [ 723a5004, 00000000, 00000001, 00000030 ]
4 [ 0053, fff0, 0005, ffc6, ff89, ff8f, ff71, 0006 ] [ 723ab601, 00000000, 000065fd, 00000030 ]

'''

import acq400_hapi
import numpy as np
import os
import time
import argparse
import sys
import shutil


def str_hex(xarr):
    uview = xarr.view(dtype=(np.uint16 if xarr.dtype == np.int16 else np.uint32))
    dfmt = ("{:04x}"  if xarr.dtype == np.int16 else "{:08x}")
    dfmte = dfmt + " ]"
    dfmt = dfmt + ", "
    #print("dtype: {} dfmt {}".format(xarr.dtype, dmft))
    txt = "[ "
    for xx in uview[:-1]:
        txt += dfmt.format(xx)
    
    return txt + dfmte.format(uview[-1])

def str_dec(xarr):    
    dfmt = ("{:06d}"  if xarr.dtype == np.int16 else "{:10d}")
    dfmte = dfmt + " ]"
    dfmt = dfmt + ", "
    #print("dtype: {} dfmt {}".format(xarr.dtype, dmft))
    txt = "[ "
    for xx in xarr[:-1]:
        txt += dfmt.format(xx)
    
    return txt + dfmte.format(xarr[-1])

def run_stream(args, uut):
    for row, (chx, spx) in enumerate(uut.stream_slowmon()):
        #print("{} len {},{} type {},{} shape {},{}\n{} {}".format(row, len(chx), len(spx), chx.dtype, spx.dtype, chx.shape, spx.shape, chx, spx))
        if args.show_raw:
            if args.show_raw == 'd':
                print("{} {} {}".format(row, str_dec(chx[:args.pchan]), str_dec(spx)))
            else:
                print("{} {} {}".format(row, str_hex(chx[:args.pchan]), str_hex(spx)))

    
def run_main():
    parser = argparse.ArgumentParser(description='acq400 slowmon')
    parser.add_argument('--show_raw', default=None, type=str, help="show raw data, 'd'=decimal, 'h'=hex")
    parser.add_argument('--pchan',    default=8, type=int, help="max channels to print")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('uuts', nargs=1, help="uuts")
    args = parser.parse_args()
    
    uut = acq400_hapi.factory(args.uuts[0])
    run_stream(args, uut)


if __name__ == '__main__':
    run_main()