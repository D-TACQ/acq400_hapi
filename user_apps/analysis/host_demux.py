#!/usr/bin/env python

""" host_demux.py Demux Data on HOST Computer

  - data is stored locally, either from mgtdram/ftp or fiber-optic AFHBA404
  - channelize the data
  - optionally store file-per-channel
  - optionally plot in pykst
  - @@todo store to MDSplus as segments.

example usage::

    ./host_demux.py --save=DATA --nchan=32 --nblks=-1 --pchan=none acq2106_067
        # load all blocks, save per channel to subdirectory DATA/data_CC.dat

    ./host_demux.py --nchan=32 --nblks=4 --pchan=1:8 acq2106_067
        # plot channels 1:8, 4 blocks


    ./host_demux.py --nchan=32 --nblks=-1 --pchan=1,2 acq2106_067
        # plot channels 1,2, ALL blocks
        # works for 8GB data, best to LIMIT the number of channels ..

    ./host_demux.py --nchan=96 --src=/data/ACQ400DATA/1 \
        --egu=1 --xdt=2e-6 --cycle=1:4 --pchan=1:2 \
        acq2106_061
        # plot AFHBA404 data from PORT1
        # plot egu (V vs s), specify interval, plot 4 cycles, plot 2 channels
        # uut

    use of --src
        --src=/data                     # valid for FTP upload data
        --src=/data/ACQ400DATA/1 	# valid for SFP data, port 1

usage:: 

    host_demux.py [-h] [--nchan NCHAN] [--nblks NBLKS] [--save SAVE]
                     [--src SRC] [--pchan PCHAN]
                     uut

host demux, host side data handling

positional arguments:
  uut            uut

optional arguments:
  -h, --help     show this help message and exit
  --nchan NCHAN
  --nblks NBLKS
  --save SAVE    save channelized data to dir
  --src SRC      data source root
  --pchan PCHAN  channels to plot
  --egu EGU      plot egu (V vs s)
  --xdt XDT      0: use interval from UUT, else specify interval

    

"""

import pykst
import numpy as np
import os
import re
import argparse
import subprocess
import acq400_hapi
import time

NSAM = 0
WSIZE = 2

def channel_required(args, ch):
#    print("channel_required {} {}".format(ch, 'in' if ch in args.pc_list else 'out', args.pc_list))
    return args.save != None or ch in args.pc_list

def create_npdata(args, nblk, nchn):
    channels = []

    for counter in range(nchn):
       if channel_required(args, counter):
           channels.append(np.zeros((nblk*NSAM), dtype=np.int16))
       else:
           # token spacer reduces memory use
           channels.append(np.zeros(16, dtype=np.int16))
    # print "length of data = ", len(total_data)
    # print "npdata = ", npdata
    return channels 


def make_cycle_list(args):
    if args.cycle == None:
        cyclist = os.listdir(args.uutroot)
        cyclist.sort()
        return cyclist
    else:
        rng = args.cycle.split(':')
        if len(rng) > 1:
            cyclist = [ '{:06d}'.format(c) for c in range(int(rng[0]), int(rng[1])+1) ]
        elif len(args.cycle) == 6:
            cyclist = [ args.cycle ]
        else:
            cyclist = [ '{:06d}'.format(int(args.cycle)) ]

        return cyclist

def get_file_names(args):
    fnlist = list()
# matches BOTH 0.?? for AFHBA an 0000 for FTP
    datapat = re.compile('[.0-9]{4}$')
    for cycle in make_cycle_list(args):
        if cycle == "err.log":
            continue
        uutroot = '{}/{}'.format(args.uutroot, cycle)
        print("debug")
        ls = os.listdir(uutroot)
        print("uutroot = ", uutroot)
        ls.sort()
        for n, file in enumerate(ls):
            if datapat.match(file):
                fnlist.append( '{}/{}'.format(uutroot, file) )
            else:
                print("no match {}".format(file))

    return fnlist

def read_data(args):
    global NSAM
    NCHAN = args.nchan
    data_files = get_file_names(args)
    for n, f in enumerate(data_files):
        print(f)
    if NCHAN % 3 == 0:
        print("collect in groups of 3 to keep alignment")
        GROUP = 3 
    else:
        GROUP = 1
    

    if NSAM == 0:
        NSAM = GROUP*os.path.getsize(data_files[0])/WSIZE/NCHAN
        print("NSAM set {}".format(NSAM))

    NBLK = len(data_files)
    if args.nblks > 0 and NBLK > args.nblks:
        NBLK = args.nblks
        data_files = [ data_files[i] for i in range(0,NBLK) ]

    print("NBLK {} NBLK/GROUP {} NCHAN {}".format(NBLK, NBLK/GROUP, NCHAN))
  
    raw_channels = create_npdata(args, NBLK/GROUP, NCHAN)
    blocks = 0
    i0 = 0
    iblock = 0
    for blknum, blkfile in enumerate(data_files):
        if blocks >= NBLK:
            break
        if blkfile != "analysis.py" and blkfile != "root":

            print blkfile, blknum
            # concatenate 3 blocks to ensure modulo 3 channel align
            if iblock == 0:
                data = np.fromfile(blkfile, dtype=np.int16)
            else:
                data = np.append(data, np.fromfile(blkfile, dtype=np.int16))

            iblock += 1
            if iblock < GROUP:
                continue
                
            i1 = i0 + NSAM
            for ch in range(NCHAN):
                if channel_required(args, ch):
                    raw_channels[ch][i0:i1] = (data[ch::NCHAN])
                # print x
            i0 = i1
            blocks += 1
            iblock = 0

    print "length of data = ", len(raw_channels)
    print "length of data[0] = ", len(raw_channels[0])
    print "length of data[1] = ", len(raw_channels[1])
    return raw_channels
    
def save_data(args, raw_channels):
    subprocess.call(["mkdir", "-p", args.saveroot])
    for enum, channel in enumerate(raw_channels):
        data_file = open("{}/data_{:02d}.dat".format(args.saveroot, enum+1), "wb+")
        channel.tofile(data_file, '')

    return raw_channels
    

def plot_data(args, raw_channels):
    client = pykst.Client("NumpyVector")
    llen = len(raw_channels[0])
    if args.egu == 1:
        if args.xdt == 0:
            time1 = float(args.the_uut.s0.SIG_CLK_S1_FREQ.split(" ")[-1])
            xdata = np.linspace(0, llen/time1, num=llen)
        else:
            xdata = np.linspace(0, llen*args.xdt, num=llen)
        xname= 'time'
        yu = 'V'
        xu = 's'
    else:
        xname = 'idx'
        yu = 'code'
        xu = 'sample'
        xdata = np.arange(0, llen).astype(np.float64)

    V1 = client.new_editable_vector(xdata, name=xname)

    for ch in [ int(c) for c in args.pc_list]:
        channel = raw_channels[ch]
        ch1 = ch+1
        if args.egu:
            # chan2volts ch index from 1:
            channel = args.the_uut.chan2volts(ch1, channel)
        # label 1.. (human)
        V2 = client.new_editable_vector(channel.astype(np.float64), name="CH{:02d}".format(ch1))
        c1 = client.new_curve(V1, V2)
        p1 = client.new_plot()
        p1.set_left_label(yu)
        p1.set_bottom_label(xu)  
        p1.add(c1)


def process_data(args):
    raw_data = read_data(args)
    if args.save != None:
        save_data(args, raw_data)
    if len(args.pc_list) > 0:
        plot_data(args, raw_data)

def make_pc_list(args):
    # ch in 1.. (human)
    if args.pchan == 'none':
        return list()
    if args.pchan == 'all':
        return list(range(0,args.nchan))
    elif len(args.pchan.split(':')) > 1:
        lr = args.pchan.split(':')
        x1 = 1 if lr[0] == '' else int(lr[0])
        x2 = args.nchan+1 if lr[1] == '' else int(lr[1])+1
        return list(range(x1, x2))
    else:
        return args.pchan.split(',') 
    
def run_main():
    parser = argparse.ArgumentParser(description='host demux, host side data handling')
    parser.add_argument('--nchan', type=int, default=32)
    parser.add_argument('--nblks', type=int, default=-1)
    parser.add_argument('--save', type=str, default=None, help='save channelized data to dir')
    parser.add_argument('--src', type=str, default='/data', help='data source root')
    parser.add_argument('--cycle', type=str, default=None, help='cycle from rtm-t-stream-disk')
    parser.add_argument('--pchan', type=str, default=':', help='channels to plot')
    parser.add_argument('--egu', type=int, default=0, help='plot egu (V vs s)')
    parser.add_argument('--xdt', type=float, default=0, help='0: use interval from UUT, else specify interval ')
    parser.add_argument('uut', nargs=1, help='uut')
    args = parser.parse_args()
    args.uutroot = "{}/{}".format(args.src, args.uut[0])
    print("uutroot {}".format(args.uutroot))
    if args.save != None: 
        if args.save.startswith("/"):
            args.saveroot = args.save
        else:
            args.saveroot = "{}/{}".format(args.uutroot, args.save)
    # ch 0.. (comp)
    args.pc_list = [ int(i)-1 for i in make_pc_list(args)]
    print("args.pc_list {}".format(args.pc_list))
    if args.egu:
        args.the_uut = acq400_hapi.Acq2106(args.uut[0])
    process_data(args)

if __name__ == '__main__':
    run_main()

