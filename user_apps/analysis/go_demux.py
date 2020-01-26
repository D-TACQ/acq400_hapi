#!/usr/bin/env python

"""
A python script to demux the data from the GO system.

Data Format

CH01 .. CH02 .. CH03 .. CH16 .. DI32 ..  SAMPLE ..usec .. fill
short   short   short   short   long     long     long    long

Usage:
Linux:
./go_demux.py --data_file="./GO_DATA/event-1-50000-50000.dat"

Windows:
python .\go_demux.py --data_file="C:/O_DATA/event-1-50000-50000.dat"
"""

from __future__ import division

import numpy as np
import matplotlib.pyplot as plt
import argparse
import acq400_hapi
import os
import re
import time


def save_data(args):
    args.raw.tofile(args.data_file)
    return None


def plot_data(args):
    # plot all the data in order (not stacked)

    axes = (
     	( "CH09", args.shorts,  8 ),
	( "CH16", args.shorts, 15 ),
	( "DI32", args.longs,   args.L0+0 ),
        ( "NSAM", args.longs,   args.L0+1 ),
        ( "usec", args.longs,   args.L0+2 ),
        ( "msec", args.longs,   args.L0+3 )
    )
    nsp = len(axes)
  
    
    print("plot_data")
    f, plots = plt.subplots(nsp, 1)
    plots[0].set_title("GO DATA {} {}".format(args.uut.uut if args.uut else "", args.data_file))

    for sp in range(0,nsp):
        (label, arr, idx) = axes[sp]
        plots[sp].plot(arr[:,idx])
        plots[sp].set(ylabel=label)

    plt.show()
    return None

def print_es(args, esp):
    rr = args.show_transitions//2
    for ii in range(esp-rr,esp+rr+1):
        txt = "{:6d}: ".format(ii)
        for jj in range(0, args.SAMPLE_SIZE_LONGS):
            txt += "{:08x}{}".format(args.longs[ii,jj], ',' if jj<args.SAMPLE_SIZE_LONGS-1 else '')
        print(txt)

def show_transitions(args):
    print("show_transitions")
#    MAGIC=0xaa55
    MAGIC1=0xaa55f151
    MAGIC2=0xaa55f152
    es1 = np.where(args.longs[:,0] == MAGIC1)
    es2 = np.where(args.longs[:,0] == MAGIC2)

    for ii in es1[0]:
        if args.longs[ii,1] == MAGIC1 and args.longs[ii,2] == MAGIC1: 
            print_es(args, ii)

    for ii in es2[0]:
        if args.longs[ii,1] == MAGIC2 and args.longs[ii,2] == MAGIC2:
            print_es(args,ii)



def make_shorts(args, shorts):
    args.shorts = np.reshape(shorts, (len(shorts)//args.SAMPLE_SIZE_SHORTS, args.SAMPLE_SIZE_SHORTS))[:,0:args.SHORTCOLS]

def make_longs(args, longs):
#    args.longs = np.reshape(longs, (len(longs)/args.SAMPLE_SIZE_LONGS, args.SAMPLE_SIZE_LONGS))[:,args.SHORTCOLS/2:]
    args.longs = np.reshape(longs, (len(longs)//args.SAMPLE_SIZE_LONGS, args.SAMPLE_SIZE_LONGS))

def uut_file_print(fn):
    # event-012-1567350364-2048-2047.dat
    m = re.search(r'event-(\d+)-([\d]+)-(\d+)-(\d+).dat', fn.decode('ISO-8859-1'))
    evnum, ts, pre, post = m.groups()

    print("fn {} ts {} event {} pre {} post {}".\
            format(fn, time.strftime('%Y%m%d:%H:%M:%S', time.gmtime(float(ts))), evnum, pre, post))

def load_data(args):
    uut_file_print(args.data_file)

    with open(args.data_file, "rb") as bf:
        args.raw = bf.read()

    make_shorts(args, np.frombuffer(args.raw, dtype=np.int16))
    make_longs(args, np.frombuffer(args.raw, dtype=np.uint32))

def uut_get_next(args, uut):
    port = acq400_hapi.AcqPorts.MULTI_EVENT_DISK if args.get_stick == 1 else acq400_hapi.AcqPorts.MULTI_EVENT_TMP
    # unfortunately ChannelClient port is based from DATA0
    client = acq400_hapi.ChannelClient(uut.uut, port-acq400_hapi.AcqPorts.DATA0)
    raw = client.read(0, data_size=4)
    args.data_file=os.path.basename(raw[:args.SAMPLE_SIZE_LONGS].tobytes()).strip()
    uut_file_print(args.data_file)
    args.raw = raw[args.SAMPLE_SIZE_LONGS:]
    make_longs(args, args.raw)
    make_shorts(args, np.frombuffer(args.raw.tobytes(), dtype=np.int16))

def uut_get_oneshot(args, uut):
    client = acq400_hapi.ChannelClient(uut.uut, 0)
    print("reading data, this may take a minute")
    raw = client.read(0, data_size=4)
    print("we have data {} lw".format(len(raw)))

    pre = uut.s0.TRANS_ACT_PRE.split()[1]
    post = uut.s0.TRANS_ACT_POST.split()[1]
    args.data_file='event-1-{}-{}-{}.dat'.format(uut.s1.event_time, pre, post)

    uut_file_print(args.data_file)
    args.raw = raw[args.SAMPLE_SIZE_LONGS:]
    make_longs(args, args.raw)
#    make_shorts(args, np.frombuffer(args.raw.tobytes(), dtype=np.int16))
   
def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--SHORTCOLS', default=16, type=int, help="number of shorts cols")
    parser.add_argument('--LONGCOLS', default=4, type=int, help="number of longs cols")
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--show_transitions', default=0, type=int, help="hexdump +/-N samples at transition")
    parser.add_argument('--data_file', default=None, type=str, help="Name of data file")
    parser.add_argument('--get_oneshot', default=None, type=str, help="[uut] pull oneshot data")
    parser.add_argument('--get_next', default=None, type=str, help="[uut] get next mv file from uut")
    parser.add_argument('--get_count', default=1, type=int, help="number of event files to fetch")
    parser.add_argument('--get_stick', default=1, type=int, help="1: get data from USB stick, 0: from /tmp")

    args = parser.parse_args()
    args.SAMPLE_SIZE = int(args.SHORTCOLS*2 + args.LONGCOLS*4)
    args.SAMPLE_SIZE_SHORTS = int(args.SHORTCOLS + 2*args.LONGCOLS)
    args.SAMPLE_SIZE_LONGS = int(args.SHORTCOLS//2 + args.LONGCOLS)
    args.L0 = int(args.SHORTCOLS//2)
    args.fn = "save_file"
    args.uut = None
    first_time = True
    if not args.get_next:
        args.get_count = 0
     
    while first_time or args.get_count > 0:
        if args.get_oneshot:
            args.uut = acq400_hapi.Acq400(args.get_oneshot)
            args.save = 1
            args.get_count = 0
            uut_get_oneshot(args, args.uut)
        elif args.get_next:
            args.uut = acq400_hapi.Acq400(args.get_next)
            args.save = 1
            uut_get_next(args, args.uut)
            args.get_count = args.get_count - 1
        elif args.data_file:
            data = load_data(args)

        if args.show_transitions > 0:
            show_transitions(args)
        if args.plot == 1:
            plot_data(args)
        if args.save == 1:
            save_data(args)
        first_time = False

if __name__ == '__main__':
    run_main()
