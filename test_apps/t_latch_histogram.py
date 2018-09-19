#!/usr/bin/env python

"""
This is a script intended to pull off the LLC T_LATCH data, calculate the delta times and plot them in a histogram.
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
        if num == 0 or item == -32768 or item == 32767:
            continue
        if item == t_latch[num-1] - 1 or item == t_latch[num-1] + 1:
            continue
        else:
            diff = item - t_latch[num-1]

            if diff in histo:
                histo[diff] += 1
            else:
                histo[diff] = 1
    return histo


def collect_tlatch(args):
    home = expanduser("~")
    data = np.fromfile(home+"/"+args.root, dtype=np.int16)
    # stride through the data in steps of nchan - 1 (since 0 indexed) - 31 (for position of T_LATCH)
    t_latch = data[args.nchan-1-31::args.nchan]
    return t_latch


def run_analysis(args):
    tlatch = collect_tlatch(args)
    histo = collect_dtimes(tlatch, args)
    plot_histogram(histo, args)
    return None


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    parser.add_argument('--root', default="PROJECTS/AFHBA404/afhba.0.log", type=str, help="Location to pull data "
                                                                                          "from for analysis.")
    parser.add_argument('--nchan', default=160, type=int, help="How many channels are contained in the data.")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    # parser.add_argument('uuts', nargs='+', help="uuts")
    run_analysis(parser.parse_args())


if __name__ == '__main__':
    run_main()
