#!/usr/bin/env python

"""
A python script to demux the data from the corescan system.

The data is supposed to come out in the following way:

CH01 .. CH02 .. CH03 .. CH04 .. INDEX .. FACET .. SAM COUNT .. usec COUNT
short   short   short   short   long     long     long          long

Usage:

python cs_demux.py --df="/home/sean/PROJECTS/workspace/acq400_hapi-1/user_apps/
                                    acq400/acq1001_068/000001/0000"

"""

import numpy as np
import matplotlib.pyplot as plt
import argparse

def find_zero_index(args):
    # This function finds the first 0xaa55f154 short value in the data and then
    # uses it's position to check the index before this event sample and the
    # index after this event sample and checks the latter is one greater
    # than the former. If the values do not increment then go to the next
    # event sample and repeat.

    data = np.fromfile(args.df, dtype=np.uint32)
    for long_pos, long_val in enumerate(data):
        long = format(long_val, '08x')
        # print "long_val = ", long
        if long_val == 0xaa55f154:
            # Check current index
            first_es_position = long_pos
            # print "first es position found @ ", first_es_position
            break

    # loop over all the event samples. Look at the "index" value before and
    # after and check they have incremented.
    counter = 0
    for pos, f_long_in_es in enumerate(data):
        if pos < first_es_position:
            continue
        if counter % (args.tl*6 + 24) == 0:
            counter += 1
            if data[pos - 3] + 1 == data[pos + 27]:
                zero_index_long_pos = pos
                return zero_index_long_pos
        else:
            counter += 1
            continue


def demux_data(args, zero_index):
    data = []
    # chunk = [1]
    count = 0

    with open(args.df, "rb") as f:
        # throw away all data before the "zeroth" index (the first es)
        chunk = np.fromfile(f, dtype=np.int32, count=int(zero_index))
        while len(chunk) != 0: # if chunk size is zero we have run out of data

            #throw away es
            if count % args.tl == 0:
                chunk = np.fromfile(f, dtype=np.int32, count=24) # strip es
                # print ""
                # for item in chunk:
                #
                #     print "{}".format(item, '08x')

            # collect data into a new list
            chunk = np.fromfile(f, dtype=np.int16, count=4)
            data.extend(chunk)
            chunk = np.fromfile(f, dtype=np.int32, count=4)
            data.extend(chunk)
            count += 1
        f.close() # close file when all the data has been loaded.
    return data


def save_data(args, data):
    np.tofile("test_file", data)
    return None


def plot_data(args, data):
    # plot all the data in order (not stacked)
    f, plots = plt.subplots(8, 1)
    for sp in range(0,8):
        plots[sp].plot(data[sp:-1:8])

    # plot all the data in stacks (one stack on top of the other)

    # burst_data = [[],[],[],[],[],[],[],[]]
    # bursted_channels = [[],[],[],[],[],[],[],[]]
    # for ch in range(0, 7):
    #     burst_data[ch].extend(data[ch:-1:8])

    # for ch in range(0, 7):
    #     count = 0
    #     for item in burst_data[ch][0:-1:args.tl]:
    #         bursted_channels[ch].append(burst_data[ch][count:count+args.tl])
    #
    # plt.plot(bursted_channels[0])
    # plt.show()
    #


    # num_bursts = len(burst_data[1]) #/float(args.tl)
    # print "num_bursts = ", num_bursts
    #
    #
    # for ch in range(0, 7):
    #
    #     for ch_num, ch in enumerate(burst_data):
    #         burst = 0
    #         counter = 0
    #         # burst_data[ch] = np.array_split(np.array(burst[0]), len(burst_data[0])/args.tl)
    #         for sample in ch:
    #             if counter < args.tl + 1:
    #                 print "sample = ", sample
    #                 print "bursted_channels[burst]", bursted_channels[burst]
    #                 bursted_channels[burst].extend(sample)
    #                 counter += 1
    #             else:
    #                 counter = 0
    #                 burst += 1
    #         print "bursted_channels = ", bursted_channels
    #
    # num_bursts = len(burst_data[0])
    #
    # print "num_bursts = ", num_bursts
    # f, plots = plt.subplots(8, 1)
    # for sp in range(0, 8):
    #
    #     # for burst in range():
    #     for burst in range(sp, len(burst_data[0]) - 1): # loop over data
    #         plots[sp].plot(data[ssp:ssp+args.tl-1:8]) # plot in blocks of 8192
    #         # plt.plot(data[ssp:ssp+8192-1:7]) # plot in blocks of 8192
    plt.show()
    return None


def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--tl', default=8192, type=int, help='transient length')
    parser.add_argument('--df', default="./shot_data", type=str, help="Name of"
                                                                    "data file")

    args = parser.parse_args()

    # zero_index should be the index of the first event sample where the
    # system value index increments over the event sample.
    zero_index = find_zero_index(args)

    # data = long list of CH01, CH02, CH03, CH04, INDEX, FACET, USEC
    data = demux_data(args, zero_index)
    if args.plot == 1:
        plot_data(args, data)
    if args.save == 1:
        save_data(args, data)

if __name__ == '__main__':
    run_main()
