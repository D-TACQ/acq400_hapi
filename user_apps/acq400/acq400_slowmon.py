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

[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --egu=1 --pchan=8 acq2106_178 | head
0, -7.52828e-04,-1.47888e-03,-7.92902e-04,-4.81650e-04,-7.51480e-04,-9.10488e-04,-7.71380e-04,-1.01143e-03
1, -6.29032e-04,-1.47888e-03,-7.92902e-04,-3.58180e-04,-7.51480e-04,-7.87045e-04,-7.71380e-04,-1.25875e-03
2, -2.57644e-04,-4.90988e-04,-5.24180e-05,-1.11240e-04,-3.80620e-04,-1.69830e-04,-4.00040e-04,-2.69477e-04
3, -2.57644e-04,-6.14475e-04,-2.99246e-04,3.82640e-04,-2.57000e-04,7.70560e-05,-2.76260e-04,-1.45818e-04


** set runtime to 10s (from first rx sample)

[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --runtime=10 --show_raw=h --pchan=8 acq2106_178
0 [ 005b, fff0, 0007, ffc5, ff8c, ff93, ff75, 0008 ] [ 101e3401, 00000000, 101e3401, 00000077 ]
1 [ 005c, fff7, 000d, ffca, ff90, ff97, ff75, 0010 ] [ 101e3402, 00000000, 00000001, 00000077 ]
2 [ 0055, ffec, 0001, ffc1, ff88, ff8f, ff70, 0006 ] [ 101e3403, 00000000, 00000001, 00000077 ]
...
1534 [ 0057, ffee, 0005, ffc2, ff89, ff94, ff6e, 0003 ] [ 10b6ce03, 00000000, 00000001, 0000003a ]
1535 [ 0057, fff4, 0007, ffc8, ff8f, ff95, ff75, 0009 ] [ 10b6ce04, 00000000, 00000001, 0000003a ]
1536 [ 0054, ffeb, ffff, ffbf, ff8a, ff8f, ff6d, 0003 ] [ 10b73401, 00000000, 000065fd, 0000003b ]


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

def to_egu(uut, xarr):
    egu = [ "{:.5e}".format(uut.chan2volts(ix+1, xx)) for ix, xx in enumerate(xarr)]
    return ",".join(egu)

def run_stream(args, uut):
    t_run = 0
    
    for row, (chx, spx) in enumerate(uut.stream_slowmon()):
        
        if row == 0:
            t0 = time.time()
        else:
            t_run = time.time() - t0
        #print("{} len {},{} type {},{} shape {},{}\n{} {}".format(row, len(chx), len(spx), chx.dtype, spx.dtype, chx.shape, spx.shape, chx, spx))
        if args.show_raw:
            if args.show_raw == 'd':
                print("{} {} {}".format(row, str_dec(chx[:args.pchan]), str_dec(spx)))
            else:
                print("{} {} {}".format(row, str_hex(chx[:args.pchan]), str_hex(spx)))
                
        if args.egu == 1:
            print("{}, {}".format(row, to_egu(uut, chx[:args.pchan])))
            
        if t_run >= args.runtime:
            return

    
def run_main():
    parser = argparse.ArgumentParser(description='acq400 slowmon')
    parser.add_argument('--show_raw', default=None, type=str, help="show raw data, 'd'=decimal, 'h'=hex")
    parser.add_argument('--pchan',    default=8, type=int, help="max channels to print")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('--egu', type=int, default=0, help='plot egu (V vs s)')
    parser.add_argument('uuts', nargs=1, help="uuts")
    args = parser.parse_args()
    
    uut = acq400_hapi.factory(args.uuts[0])
    run_stream(args, uut)


if __name__ == '__main__':
    run_main()