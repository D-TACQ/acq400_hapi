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




def save_data(args):
    np.tofile("test_file", data)
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
            plots[sp].plot(args.longs[:,0])
        if sp==3:
            plots[sp].plot(args.longs[:,2])

        plots[sp].set(ylabel=axes[sp] )
    plt.show()
    return None

def show_transitions(args):
    MAGIC=0xaa55
    es1 = np.where(args.shorts[:,0] == MAGIC)

    print("es1 {}".format( es1[0] ))
    es3 = np.where(args.shorts[:,1] == MAGIC)
    print("es3 {}".format( es3[0] ))
    print es3


def load_data(args):
    with open(args.data_file, "rb") as bf:
        args.raw = bf.read()

    shorts = np.frombuffer(args.raw, dtype=np.int16)
    args.shorts = np.reshape(shorts, (len(shorts)/args.SAMPLE_SIZE_SHORTS, args.SAMPLE_SIZE_SHORTS))[:,0:args.SHORTCOLS]

    longs = np.frombuffer(args.raw, dtype=np.uint32)
    args.longs = np.reshape(longs, (len(longs)/args.SAMPLE_SIZE_LONGS, args.SAMPLE_SIZE_LONGS))[:,args.SHORTCOLS/2:]

def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--SHORTCOLS', default=16, type=int, help="number of shorts cols")
    parser.add_argument('--LONGCOLS', default=4, type=int, help="number of longs cols")
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--show_transitions', default=0, type=int, help="hexdump +/-N samples at transition")
    parser.add_argument('--data_file', default="./shot_data", type=str, help="Name of data file")
#    parser.add_argument('--get_next', default=none, type=str, help="[uut] get next mv file from uut")

    args = parser.parse_args()
    args.SAMPLE_SIZE_SHORTS = args.SHORTCOLS + 2*args.LONGCOLS
    args.SAMPLE_SIZE_LONGS = args.SHORTCOLS/2 + args.LONGCOLS

 

    data = load_data(args)

    if args.show_transitions > 0:
        show_transitions(args)
    if args.plot == 1:
        plot_data(args)
    if args.save == 1:
        save_data(args)

if __name__ == '__main__':
    run_main()
