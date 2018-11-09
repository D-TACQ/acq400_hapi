#!/usr/bin/env python

"""
A python script to demux the data from the corescan system.

The data is supposed to come out in the following way:

CH01 .. CH02 .. CH03 .. CH04 .. INDEX .. FACET .. COUNT
short   short   short   short   long     long     long
"""

import numpy as np
import matplotlib.pyplot as plt
import argparse

def find_zero_index(args):
    # This function finds the first 0xaa55 short value in the data and then
    # uses this position to check the index before this event sample and the
    # index after this event sample and checks the latter is one greater
    # than the former. If the values do not increment then go to the next
    # event sample

    data = np.fromfile(args.df, dtype=np.uint32)
    for short_pos, short_val in enumerate(data):
        short = format(short_val, '08x')
        print "short_val = ", short
        if short_val == 0xaa55f154:
            # if count < 4:
            #     continue
            # Check current index
            first_es_position = short_pos
            print "first es position found @ ", first_es_position
            break

    # loop over all the event samples. Look at the "index" value before and
    # after and check they have incremented.
    #for pos, f_short_in_es in enumerate(data[first_es_position:-1:((10*8192)+(9+(10*3)))]):
    counter = 0
    for pos, f_short_in_es in enumerate(data):
        if pos < first_es_position:
            continue
        if counter % (49212 + 24) == 0: # TODO: Ask Scott why this is

            #print "counter - ", counter, " value = ", f_short_in_es
            print "DEBUG: pre = ", data[pos - 3], " post = ", data[pos + 27]
            counter += 1
            if data[pos - 3] + 1 == data[pos + 27]:
                zero_index_long_pos = pos
                print "zisp = ", zero_index_long_pos
                return zero_index_long_pos
        else:
            counter += 1
            continue


def demux_data(args, zero_index):
    data = []
    chunk = [1]
    count = 0

    with open(args.df, "rb") as f:
        # throw away all data before the "zeroth" index (the first es)
        chunk = np.fromfile(f, dtype=np.int32, count=int(zero_index))

        while len(chunk) != 0: # if chunk size is zero we have run out of data

            #throw away es
            if count % 8202 == 0: # Should be 8202?
                chunk = np.fromfile(f, dtype=np.int32, count=24) # strip es
                print ""
                for item in chunk:

                    print "{}".format(item, '08x')

            # collect data into a new list
            chunk = np.fromfile(f, dtype=np.int16, count=4)
            data.extend(chunk)
            chunk = np.fromfile(f, dtype=np.int32, count=4)
            data.extend(chunk)
            #print "chunk = ", chunk
            count += 1
        #print "data = ", data
        f.close() # close file when all the data has been loaded.
    return data


def save_data(args, data):
    np.tofile("test_file", data)
    return None


def plot_data(args, data):
    # plot all the data in order (not stacked)

    # f, plots = plt.subplots(8, 1, sharex=True)

    f, plots = plt.subplots(8, 1)
    for sp in range(0,8):
        plots[sp].plot(data[sp:-1:8])

        #plt.subplot((sp*100)+11)
        #plt.plot(data[sp-1:-1:8])

    # plt.plot(data[7:-1:8])

    # plot all the data in stacks (one stack on top of the other)
    # for sp in range(0,6):
    #     plt.subplot(sp)
    #     for ssp in range(0:len(data)-1:8192): # loop over data in 8192 blocks
    #         plt.plot(data[ssp:ssp+8192-1:7]) # plot in blocks of 8192
    plt.show()
    return None


def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--tl', default=8202, type=int, help='transient length')
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
