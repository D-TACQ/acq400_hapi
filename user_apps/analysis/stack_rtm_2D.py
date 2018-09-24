#!/usr/bin/python
'''
acq480 2D data is unique in that channels "double tap", so demux is .. tricky.
best practise is to demux on the box
what about rgm?. OK, download the demux data then reconstruct the ES
eg
./user_apps/acq400/set_burst.py --config_only 1 --rgm RTM --rtm_translen=250 --dx=d0 --sense=rising --trace=1 $UUTS

./user_apps/acq400/acq400_upload.py --trace_upload=1 --plot_data=1 --capture=-1 --save_data=./DATA/ $UUTS

Gives us:
pgm@hoy5 acq400_hapi]$ ls -l DATA
total 6276
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH01
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH02
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH03
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH04
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH05
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH06
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH07
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_148_CH08
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH01
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH02
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH03
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH04
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH05
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH06
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH07
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_149_CH08
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_278_CH01
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_278_CH02
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:19 acq1001_278_CH03
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_278_CH04
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_278_CH05
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_278_CH06
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_278_CH07
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_278_CH08
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH01
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH02
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH03
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH04
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH05
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH06
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH07
-rw-rw-r-- 1 pgm pgm 200000 Sep 24 11:20 acq1001_279_CH08

ES magic is present in even channels only
[pgm@hoy5 acq400_hapi]$ hexdump DATA/acq1001_148_CH01 | grep aa55 | head
[pgm@hoy5 acq400_hapi]$ 
pgm@hoy5 acq400_hapi]$ hexdump DATA/acq1001_148_CH06 | grep aa55 | head
0000000 fe44 fe44 f154 aa55 fe44 fe4c fe48 fe44
00003f0 f154 aa55 fe44 fe48 fe48 fe48 fe44 fe48
00007d0 fe48 fe44 fe40 fe44 fe48 fe44 f154 aa55
0000bc0 fe44 fe44 fe40 fe40 f154 aa55 fe44 fe48

PLAN:
- load all the files as int16
- recast the CHeven to int32, locate and compare ES magic.

- then restack all the data as

data[UUT][CHX][BURST][t]

Then plot it any way you like.
'''

import numpy as np
import os
import re
import argparse
import subprocess
import acq400_hapi
import time

def get_src_names(root):
    p = re.compile('.*_CH[0-9][0-9]$')
    src_names = []
    for name in  os.listdir(root):
        if p.match(name):
            src_names.append(name)
            
    src_names.sort()
   
    return src_names

def get_esi(chx):
# calculate ES indices    
    esi = [ [] for ii in range(len(chx))]
    for ich, ch in enumerate(chx):
        for ii in range(0, len(ch)):
            if ch[ii] == 0xaa55f154:
#                print("es at {}".format(ii))
                esi[ich].append(ii)
    
    lmin = len(esi[0])
    truncate = False
    
    for ll in [ len(esi[ii]) for ii in range(1, len(esi))]:
        if ll != lmin:
            lmin = min(ll, lmin)
            print("WARNING: burst count mismatch, min is {}".format(lmin))
            truncate = True

    bmin = esi[0][1] - esi[0][0]
    
    for bl in [ esi[0][ii]-esi[0][ii-1] for ii in range(2,len(esi))]:
        if bl != bmin:
            bmin = min(bl, bmin)
            print("WARNING bmin set {}".format(bmin))
    return lmin,bmin, esi


def get_data(args):
    srcs = get_src_names(args.root)
    nchan = len(srcs)
    raw = [ np.fromfile("{}/{}".format(args.root, srcs[ii]), dtype=np.int16) for ii in range(0, nchan)]
    nbursts, blen, esi = get_esi([ np.fromfile("{}/{}".format(args.root, srcs[ii]), dtype=np.uint32) for ii in range(1,nchan, 2)])
    chx = np.zeros((nchan, nbursts, blen))
    esi0 = esi[0]
    print(esi0)
    for ic in range(nchan):
        for ib in range(nbursts):
            for ii in range(blen):                
                chx[ic, ib, ii] = raw[ic][esi0[ib]+2+ii]
                
    return chx
    
def plot_data(chx, args):
    print("PLOT")
    
def process_data(args):
    chx = get_data(args)
    plot_data(chx, args)
    
    
    
def run_main():
    parser = argparse.ArgumentParser(description='host demux, host side data handling')
    parser.add_argument('--root', type=str, default="./DATA", help='directory with data')
    args = parser.parse_args()
    if os.path.isdir(args.root):
        print("using data from {}".format(args.root))
        process_data(args)
    else:
        print("ERROR: --root {} is not a directory".format(args.root))
    
    
    

if __name__ == '__main__':
    run_main()
