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

    

"""

import pykst
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
import time
import gc
import re
import argparse
import subprocess

NSAM = 1048576
NBLK = 16
NCHN = 32

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


def read_data(args):
    current_dir_contents = listdir(args.uutroot)
    NCHN = args.nchan
    data_files = list()

    datapat = re.compile('[0-9]{4}')
    for blknum, blkfile in enumerate(current_dir_contents):
        if datapat.match(blkfile):
            data_files.append("{}/{}".format(args.uutroot, blkfile))

    NBLK = len(data_files)
    if args.nblks > 0 and NBLK > args.nblks:
        NBLK = args.nblks

    print("NBLK {} NCHN {}".format(NBLK, NCHN))
   
    raw_channels = create_npdata(args, NBLK, NCHN)
    blocks = 0
    i0 = 0
    for blknum, blkfile in enumerate(data_files):
        if blocks >= NBLK:
            break
        if blkfile != "analysis.py" and blkfile != "root":

            print blkfile, blknum
            data = np.fromfile(blkfile, dtype=np.int16)
            i1 = i0 + NSAM
            for ch in range(NCHN):
                if channel_required(args, ch):
                    raw_channels[ch][i0:i1] = (data[ch::32])
                # print x
            i0 = i1
            blocks += 1

    print "length of data = ", len(raw_channels)
    print "length of data[0] = ", len(raw_channels[0])
    print "length of data[1] = ", len(raw_channels[1])
    return raw_channels
    
def save_data(args, raw_channels):
    subprocess.call(["mkdir", "-p", args.saveroot])
    for enum, channel in enumerate(raw_channels):
        data_file = open("{}/data_{:02d}.dat".format(args.saveroot, enum), "wb+")
        channel.tofile(data_file, '')

    return raw_channels
    

def plot_data(args, raw_channels):
    client = pykst.Client("NumpyVector")
#    time.sleep(10)
    xdata = np.arange(0, len(raw_channels[0])).astype(np.float64)
    V1 = client.new_editable_vector(xdata, name="idx")
    ccount = 0
    for ch in [ int(c) for c in args.pc_list]:
        channel = raw_channels[ch]
        V2 = client.new_editable_vector(channel.astype(np.float64), name="CH{:02d}".format(ch+1))
        c1 = client.new_curve(V1, V2)
        p1 = client.new_plot()
        p1.add(c1)
        ccount += 1


def process_data(args):
    raw_data = read_data(args)
    if args.save != None:
        save_data(args, raw_data)
    if len(args.pc_list) > 0:
        plot_data(args, raw_data)

def make_pc_list(args):
    if args.pchan == 'none':
        return list()
    if args.pchan == 'all':
	return list(range(0,args.nchan))
    elif len(args.pchan.split(':')) > 1:
        lr = args.pchan.split(':')
        x1 = 0 if lr[0] == '' else int(lr[0])
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
    parser.add_argument('--pchan', type=str, default=':', help='channels to plot')
    parser.add_argument('uut', nargs=1, help='uut')
    args = parser.parse_args()
    args.uutroot = "{}/{}".format(args.src, args.uut[0])
    if args.save != None: 
        if args.save.startswith("/"):
            args.saveroot = args.save
        else:
            args.saveroot = "{}/{}".format(args.uutroot, args.save)
    args.pc_list = [ int(i)-1 for i in make_pc_list(args)]
    print("args.pc_list {}".format(args.pc_list))
    process_data(args)

if __name__ == '__main__':
    run_main()

