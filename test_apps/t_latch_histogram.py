#!/usr/bin/env python

"""
This is a script intended to pull off the LLC T_LATCH data, calculate the delta times and plot them in a histogram.

Usage:

Usage for 1AI BOLO with spad length of 8:
python t_latch_histogram.py --nchan=48 --spad_len=8

Usage for 4 x acq424, 2 x ao424
python t_latch_histogram.py

"""


import argparse
import numpy as np
import matplotlib.pyplot as plt
from os.path import expanduser


def plot_histogram(histo, args):
    plt.bar(histo.keys(), histo.values(), 1)
    plt.show()
    return None


def collect_dtimes(t_latch, args):
    histo = {1: 0, 2: 0, 3: 0}
    for num, item in enumerate(t_latch):
        if num == 0 or item == - 2**31 or item == 2**31-1: # Handle the case of 32 bit rollover.
            # if the number is 0 or is about to roll over then just continue to the next value.
            continue

        if item == t_latch[num-1] - 1 or item == t_latch[num-1] + 1:
            if args.ones == 0:
                # if the diff is one and the args.ones arg is set to false then continue to next value.
                continue

        diff = item - t_latch[num-1]
        if diff in histo:
            histo[diff] += 1
        else:
            histo[diff] = 1
    return histo


def collect_tlatch(args):
    if args.src == "PROJECTS/AFHBA404/afhba.0.log":
        home = expanduser("~")
        data = np.fromfile(home+"/"+args.src, dtype=np.int32)
    else:
        data = np.fromfile(args.src, dtype=np.int32)

    # stride through the data in steps of:
    # nchan/2 (real channels are shorts but we have loaded data as longs)
    t_latch = data[args.nchan/2::args.nchan/2+args.spad_len] # divide nchan by 2 as we are now dealing with long ints.
    return t_latch


def run_analysis(args):
    tlatch = collect_tlatch(args)
    histo = collect_dtimes(tlatch, args)
    plot_histogram(histo, args)
    return None


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    parser.add_argument('--ones', default=0, type=int, help="The ones argument allows the user to plot the instances "
                                                            "where the calculated t_latch difference is equal to one. "
                                                            "This is the default case and so this will dwarf the other "
                                                            "numbers in the histogram.")
    parser.add_argument('--src', default="PROJECTS/AFHBA404/afhba.0.log", type=str, help="Location to pull data "
                                                                                          "from for analysis.")
    parser.add_argument('--nchan', default=128, type=int, help="How many physical channels are contained in the data"
                                                               "EXCLUDING SCRATCHPAD.")
    parser.add_argument('--spad_len', default=16, type=int, help="How long the scratchpad is. Default is 16 long words")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    # parser.add_argument('uuts', nargs='+', help="uuts")
    run_analysis(parser.parse_args())


if __name__ == '__main__':
    run_main()
