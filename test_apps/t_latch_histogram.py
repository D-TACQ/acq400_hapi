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
            # print("Histo: {}".format(histo))
        else:
            histo[diff] = 1

    for key in histo:
        print("T_LATCH differences: ", key, ", happened: ", histo[key], " times")
    return histo


def collect_dtimes_improved(t_latch):
    # print("Hello world")
    # print(t_latch.shape[-1])
    histo = {1: 0, 2: 0, 3: 0}
    # ideal = np.arange(t_latch[0], len(t_latch))
    ideal = np.arange(t_latch[0], t_latch.shape[-1]+t_latch[0])
    if np.array_equal(t_latch, ideal):
        histo[1] += len(t_latch)
    else:
        pos = 0
        while True:
            # t_latch_test = np.subtract(ideal[pos:], t_latch[pos:])
            t_latch_test = np.subtract(ideal, t_latch)
            first_nonzero = (t_latch_test != 0).argmax(axis=0)
            if first_nonzero == 0:
                # print("Breaking")
                break
            # print("first_nonzero = {}".format(first_nonzero))
            pos = first_nonzero + 1
            diff = t_latch[first_nonzero] - ideal[first_nonzero]
            # print("t_latch[first_nonzero] = {}, ideal[first_nonzero] = {}".format(t_latch[first_nonzero], ideal[first_nonzero]))
            # print("diff = {}".format(diff))
            if diff in histo:
                histo[diff] += 1
                # print("Histo: {}".format(histo))
            else:
                histo[diff] = 1


            t_latch = t_latch[pos:]
            # ideal = ideal[pos:]
            ideal = np.arange(t_latch[0], t_latch.shape[-1]+t_latch[0])

            # print("t_latch length = {}".format(t_latch.shape[-1]))

            if t_latch.shape[-1] == 0:
                break

    # print("Done")

    # if args.ones == 1:
    #     histo[0] =
    # for key in histo:
    #     print("T_LATCH differences: ", key, ", happened: ", histo[key], " times")
    return histo


def collect_tlatch(args):
    if args.src == "PROJECTS/AFHBA404/afhba.0.log":
        home = expanduser("~")
        data = np.fromfile(home+"/"+args.src, dtype=np.int32)
    else:
        data = np.fromfile(args.src, dtype=np.int32)
        # data = np.load(args.src, dtype=np.int32, mmap_mode='r')
        t_latch = data[int(args.nchan/2)::int(args.nchan/2+args.spad_len)]

    # stride through the data in steps of:
    # nchan/2 (real channels are shorts but we have loaded data as longs)
    # t_latch = data[int(args.nchan/2)::int(args.nchan/2+args.spad_len)] # divide nchan by 2 as we are now dealing with long ints.
        #
        # data = np.array([1])
        # counter = 0
        # ncols = int((args.nchan/2) + args.spad_len)
        # read_size = int(100000*ncols)
        # file_size = int(os.path.getsize(args.src))
        # t_latch = np.zeros(int(os.path.getsize(args.src)/(ncols)))
        #
        # with open(args.src, 'rb') as fid:
        #     while data.shape[-1] != 0:
        #
        #         data = np.fromfile(fid, dtype=np.int32, count=read_size)
        #
        #         t_latch[counter:counter+int(read_size/ncols)] = data[int(args.nchan/2)::ncols]
        #
        #
        #         longs_to_go = int(file_size/80 - (counter + read_size))
        #         if longs_to_go < read_size:
        #             read_size = longs_to_go
        #             print("This should only happen once")
        #
        #         # counter += read_size
        #         counter += int(read_size/ncols)
        #         print("counter = {}".format(counter))

                # print("Counter = {}".format(counter))
                # print("longs_to_go = {}".format(longs_to_go))
    # print("T_LATCH: {}".format(t_latch[-10000:]))
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
        # for f in concurrent.futures.as_completed(results):
            # print(f.result())
            # for key in histo:
            #     print("T_LATCH differences: ", key, ", happened: ", histo[key], " times")
    # histo = collect_dtimes_improved(tlatch, args)
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
