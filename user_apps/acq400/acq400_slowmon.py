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


** set runtime to 10s (from first rx sample),

[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --runtime=10 --show_raw=h --pchan=8 acq2106_178
0 [ 005b, fff0, 0007, ffc5, ff8c, ff93, ff75, 0008 ] [ 101e3401, 00000000, 101e3401, 00000077 ]
1 [ 005c, fff7, 000d, ffca, ff90, ff97, ff75, 0010 ] [ 101e3402, 00000000, 00000001, 00000077 ]
2 [ 0055, ffec, 0001, ffc1, ff88, ff8f, ff70, 0006 ] [ 101e3403, 00000000, 00000001, 00000077 ]
...
1534 [ 0057, ffee, 0005, ffc2, ff89, ff94, ff6e, 0003 ] [ 10b6ce03, 00000000, 00000001, 0000003a ]
1535 [ 0057, fff4, 0007, ffc8, ff8f, ff95, ff75, 0009 ] [ 10b6ce04, 00000000, 00000001, 0000003a ]
1536 [ 0054, ffeb, ffff, ffbf, ff8a, ff8f, ff6d, 0003 ] [ 10b73401, 00000000, 000065fd, 0000003b ]

** dump to file:

***  .csv

[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --runtime=10 --egu=1 --show=0 --pchan=8 --save_file=stream.csv acq2106_178
[pgm@hoy5 acq400_hapi]$ head stream.csv 
0, -1.33848e-04,-6.14475e-04,1.94410e-04,-1.11240e-04,-2.57000e-04,-4.63870e-05,-1.52480e-04,2.25159e-04
1, 3.61336e-04,1.26447e-04,5.64652e-04,8.76520e-04,2.37480e-04,6.94271e-04,-2.87000e-05,4.72477e-04
2, -1.33848e-04,-8.61449e-04,-4.22660e-04,-1.11240e-04,-3.80620e-04,2.00499e-04,-4.00040e-04,-1.45818e-04
3, -8.76624e-04,-1.23191e-03,-7.92902e-04,-4.81650e-04,-8.75100e-04,-6.63602e-04,-1.01894e-03,-6.40454e-04
4, -2.57644e-04,-9.84936e-04,-4.22660e-04,-3.58180e-04,-6.27860e-04,-1.69830e-04,-6.47600e-04,-1.45818e-04

*** binary
[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_slowmon.py --runtime=10 --egu=1 --show=0 --pchan=8 --save_file=stream.dat acq2106_178
[pgm@hoy5 acq400_hapi]$ hexdump -e '32/2 "%04x," 4/4 "%08x," "\n"' stream.dat | head
004e,ffe7,fffb,ffbc,ff83,ff8a,ff69,fffe,ffcb,ff41,ffed,ff63,0051,001a,0031,0058,0155,0185,0115,0138,014d,01bd,0144,01df,01a6,00fb,0170,01d5,013b,01d9,00d8,0158,603b6001,00000000,603b6001,0000001a,
0058,fff3,0009,ffca,ff8b,ff93,ff75,000a,ffd5,ff4f,fffa,ff70,005f,0028,003e,0064,0087,00b5,0043,006b,0080,00f0,0076,0111,00dc,002f,00a2,0107,0070,010b,000e,0089,603b6002,00000000,00000001,0000001a,
0058,fff3,0005,ffcb,ff8a,ff92,ff75,0009,ffd2,ff4d,fff7,ff6d,005c,0024,003a,0063,ffbe,ffed,ff79,ffa0,ffb3,0024,ffae,0045,0012,ff64,ffdf,0043,ffa7,0045,ff45,ffc5,603b6003,00000000,00000001,0000001a,
0055,ffee,0004,ffc7,ff8a,ff92,ff70,0006,ffd4,ff4b,fff7,ff6b,0059,0023,003b,0060,fef4,ff20,feae,fed8,feeb,ff5f,fee3,ff78,ff47,fe9a,ff0f,ff70,fed9,ff78,fe7a,fef6,603b6004,00000000,00000001,0000001a,
0059,fff1,0008,ffc7,ff8e,ff95,ff74,000b,ffd7,ff4e,fff7,ff6e,0060,0027,003c,0063,f8bc,f8e4,f86e,f890,f8aa,f91c,f8a8,f93e,f90d,f863,f8d5,f939,f8a0,f93f,f845,f8bc,603bc601,00000000,000065fd,0000001a,
0057,fff2,0004,ffc6,ff90,ff94,ff74,000a,ffd4,ff4a,fff9,ff6b,005c,0024,003c,0060,f81a,f83e,f7cc,f7ef,f806,f879,f807,f8a0,f869,f7be,f832,f895,f7fc,f898,f79f,f817,603bc602,00000000,00000001,0000001a,


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
    if args.save_file:
        fn = args.save_file.format(args.uuts[0])
        csv_file = fn.endswith(".csv")
        data_file = open(fn, "w" if csv_file else "wb" )
    else:
        csv_file = 0
        
    t_run = 0
    
    for row, (chx, spx) in enumerate(uut.stream_slowmon()):
        
        if row == 0:
            t0 = time.time()
        else:
            t_run = time.time() - t0
        #print("{} len {},{} type {},{} shape {},{}\n{} {}".format(row, len(chx), len(spx), chx.dtype, spx.dtype, chx.shape, spx.shape, chx, spx))
        if args.show_raw or csv_file:
            if args.show_raw == 'd':
                txt_row = ("{} {} {}".format(row, str_dec(chx[:args.pchan]), str_dec(spx)))
            else:
                txt_row = ("{} {} {}".format(row, str_hex(chx[:args.pchan]), str_hex(spx)))
                
        if args.egu == 1:
            txt_row = ("{}, {}".format(row, to_egu(uut, chx[:args.pchan])))
            
        if args.show == 1:
            print(txt_row)
            
        if args.save_file:
            if csv_file:
                data_file.write(txt_row+"\n")
            else:
                chx.tofile(data_file)
                spx.tofile(data_file)
            
        if t_run >= args.runtime:
            return

    
def run_main():
    parser = argparse.ArgumentParser(description='acq400 slowmon')
    parser.add_argument('--show_raw', default=None, type=str, help="show raw data, 'd'=decimal, 'h'=hex")
    parser.add_argument('--show', default=1, type=int, help="show data on screen (raw or egu)")
    parser.add_argument('--pchan',    default=8, type=int, help="max channels to print")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('--egu', type=int, default=0, help='plot egu (V vs s)')
    parser.add_argument('--save_file', default=None, type=str, help="store binary output to file")
    parser.add_argument('uuts', nargs=1, help="uuts")
    args = parser.parse_args()
     
    
    uut = acq400_hapi.factory(args.uuts[0])
    run_stream(args, uut)


if __name__ == '__main__':
    run_main()