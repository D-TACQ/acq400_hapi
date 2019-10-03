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
import os
import threading
import concurrent.futures


def plot_histogram(histo, args):
    plt.bar(histo.keys(), histo.values(), 1)
    plt.title("Histogram of T_LATCH values. N > 1 means N-1 samples were missed.")
    plt.ylabel("Number of occurrences on a log scale.")
    plt.xlabel("T_LATCH differences.")
    plt.yscale("log")
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

    for key in histo:
        print("T_LATCH differences: ", key, ", happened: ", histo[key], " times")
    return histo


def collect_dtimes_improved(t_latch):
    histo = {1: 0, 2: 0, 3: 0}
    ideal = np.arange(t_latch[0], t_latch.shape[-1]+t_latch[0])
    if np.array_equal(t_latch, ideal):
        histo[1] += len(t_latch)
    else:
        pos = 0
        while True:
            t_latch_test = np.subtract(ideal, t_latch)
            first_nonzero = (t_latch_test != 0).argmax(axis=0)
            if first_nonzero == 0:
                break
            pos = first_nonzero + 1
            diff = t_latch[first_nonzero] - ideal[first_nonzero]
            if diff in histo:
                histo[diff] += 1
            else:
                histo[diff] = 1

            t_latch = t_latch[pos:]
            ideal = np.arange(t_latch[0], t_latch.shape[-1]+t_latch[0])

            if t_latch.shape[-1] == 0:
                break

    return histo


def collect_tlatch(args):
    if args.src == "PROJECTS/AFHBA404/afhba.0.log":
        home = expanduser("~")
        data = np.fromfile(home+"/"+args.src, dtype=np.int32)
    else:
        data = np.fromfile(args.src, dtype=np.int32)
        t_latch = data[int(args.nchan/2)::int(args.nchan/2+args.spad_len)]

    print("Finished collecting data")

    return t_latch


def run_analysis(args):
    tlatch = collect_tlatch(args)
    t_latch_split = np.array_split(tlatch, 8)
    histo = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # results = [executor.submit(collect_dtimes_improved, split) for split in t_latch_split]
        results = executor.map(collect_dtimes_improved, t_latch_split)
        for result in results:
            print(result)
            for key in result:
                if key in histo:
                    histo[key] += result[key]
                else:
                    histo[key] = result[key]

    for key in histo:
        print("T_LATCH differences: ", key, ", happened: ", histo[key], " times")
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
