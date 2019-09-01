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

    axes = [
    "CH09",
    "CH16",
    "DI32",
    "SAMPLE Count",
    ]
   
    print("plot_data")
    f, plots = plt.subplots(4, 1)
    plots[0].set_title("GO DATA")

    for sp in range(0,4):
        if sp==0:
            plots[sp].plot(args.shorts[:,8])
        if sp==1:
            plots[sp].plot(args.shorts[:,15])
        if sp==2:
            plots[sp].plot(args.longs[:,8+0])
        if sp==3:
            plots[sp].plot(args.longs[:,8+2])

        plots[sp].set(ylabel=axes[sp] )
    plt.show()
    return None

def print_es(args, esp):
    rr = args.show_transitions/2
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
    args.shorts = np.reshape(shorts, (len(shorts)/args.SAMPLE_SIZE_SHORTS, args.SAMPLE_SIZE_SHORTS))[:,0:args.SHORTCOLS]

def make_longs(args, longs):
#    args.longs = np.reshape(longs, (len(longs)/args.SAMPLE_SIZE_LONGS, args.SAMPLE_SIZE_LONGS))[:,args.SHORTCOLS/2:]
    args.longs = np.reshape(longs, (len(longs)/args.SAMPLE_SIZE_LONGS, args.SAMPLE_SIZE_LONGS))

def uut_file_print(fn):
    # event-012-1567350364-2048-2047.dat
    m = re.search(r'event-(\d+)-([\d]+)-(\d+)-(\d+).dat', fn)
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
    client = acq400_hapi.ChannelClient(uut.uut, 556)
    raw = client.read(0, 2)
    args.data_file=os.path.basename(raw[:args.SAMPLE_SIZE_SHORTS].tobytes()).strip()
    uut_file_print(args.data_file)
    args.raw = raw[args.SAMPLE_SIZE_SHORTS:]
    make_shorts(args, args.raw)
    make_longs(args, np.frombuffer(args.raw.tobytes(), dtype=np.uint32))

def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--SHORTCOLS', default=16, type=int, help="number of shorts cols")
    parser.add_argument('--LONGCOLS', default=4, type=int, help="number of longs cols")
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--show_transitions', default=0, type=int, help="hexdump +/-N samples at transition")
    parser.add_argument('--data_file', default=None, type=str, help="Name of data file")
    parser.add_argument('--get_next', default=None, type=str, help="[uut] get next mv file from uut")

    args = parser.parse_args()
    args.SAMPLE_SIZE = args.SHORTCOLS*2 + args.LONGCOLS*4
    args.SAMPLE_SIZE_SHORTS = args.SHORTCOLS + 2*args.LONGCOLS
    args.SAMPLE_SIZE_LONGS = args.SHORTCOLS/2 + args.LONGCOLS
    args.fn = "save_file"

    if args.get_next:
        uut = acq400_hapi.Acq400(args.get_next)
        args.save = 1
        uut_get_next(args, uut)
    elif args.data_file:
        data = load_data(args)

    if args.show_transitions > 0:
        show_transitions(args)
    if args.plot == 1:
        plot_data(args)
    if args.save == 1:
        save_data(args)

if __name__ == '__main__':
    run_main()
