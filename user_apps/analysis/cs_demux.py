#!/usr/bin/env python

"""
A python script to demux the data from the cs system.

The data is supposed to come out in the following way:

CH01 .. CH02 .. CH03 .. CH04 .. INDEX .. FACET .. SAM COUNT .. usec COUNT
short   short   short   short   long     long     long          long

Usage:
Linux:
python cs_demux.py --data_file="/home/sean/PROJECTS/workspace/acq400_hapi-1/user_apps/
                                    acq400/acq1001_068/000001/0000"
Windows:
python .\cs_demux.py --plot_facets=4 --data_file="C:/acq2106_112/000001/0000"
"""


import numpy as np
import matplotlib.pyplot as plt
import argparse

# Sample in u32
# <ACQ420    ><QEN         ><AGG        >
# <AI12><AI34><FACET><INDEX><AGSAM><USEC>

LPS = 6       # longs per sample
ESS = 4       # EVENT signature length in samples
ESL = LPS*ESS # ES length in LW

IX_AI0102 = 0
IX_AI0304 = 1
IX_FACET  = 2
IX_INDEX  = 3
IX_AGSAM  = 4
IX_USEC   = 5

PREV_INDEX = LPS-IX_INDEX   # look back to INDEX in previous sample
NEXT_INDEX = ESL+IX_INDEX   # look forward to next INDEX from beginning of ES

def isES(d):
    return d[0] == 0xaa55f154 and d[1] == 0xaa55f154 and d[2] == 0xaa55f15f and d[3] == 0xaa55f15f

def find_zero_index(args):
    # This function finds the first 0xaa55f154 short value in the data and then
    # uses its position to check the index before this event sample and the
    # index after this event sample and checks the latter is one greater
    # than the former. If the values do not increment then go to the next
    # event sample and repeat.

    data = np.fromfile(args.data_file, dtype=np.uint32)
    for pos, lvnu in enumerate(data):
        if isES(data[pos:pos+ESL]):
            # Check current index
            first_es_position = pos
            break

    print("DEBUG: first_es_position {}".format(first_es_position))
    # loop over all the event samples. Look at the "index" value before and
    # after and check they have incremented.
    next_es = args.transient_length*LPS + ESL
    
    for pos, lvnu in enumerate(data[first_es_position:]):
        if pos > 0 and pos % next_es == 0:
            if not isES(data[pos:pos+ESL]):
                print("ERROR: expected ES at {}".format(pos))
                exit(1)
            print("DEBUG: counter {} samples {}".format(pos, pos//LPS))            
            if data[pos - PREV_INDEX] + 1 == data[pos + NEXT_INDEX]:
                return pos

    print("ERROR: we do not want to be here")
    exit(1)


def demux_data(args, zero_index):
    # Demuxes the data into a single dimension list that contains the data in
    # sequence.
    data = []
    count = 0

    with open(args.data_file, "rb") as f:
        # throw away all data before the "zeroth" index (the first es)
        print("DEBUG: zero_index {} {}".format(zero_index, type(zero_index)))
        chunk = np.fromfile(f, dtype=np.int32, count=int(zero_index))
        while len(chunk) != 0: # if chunk size is zero we have run out of data

            #throw away es
            if count % args.transient_length == 0:
                chunk = np.fromfile(f, dtype=np.int32, count=24) # strip es

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

    axes = ["Demuxed channels from acq1001",
    "CH01 \n (Sampled \n FACET)",
    "CH02 \n (Sampled \n INDEX)",
    "CH03 \n (Sampled \n Sine Wave)",
    "CH04 \n (Sampled \n Sine Wave)",
    "FACET",
    "INDEX",
    "Sample Count",
    "usec Count",
    "Samples"]

    f, plots = plt.subplots(8, 1)
    plots[0].set_title(axes[0])

    for sp in range(0,8):
        if args.plot_facets != -1:
            try:
                # Plot ((number of facets) * (rtm len)) - 1 from each channel
                plots[sp].plot(data[sp:args.plot_facets * args.transient_length * 8 - 1:8])
            except:
                print("Data exception met. Plotting all data instead.")
                plots[sp].plot(data[sp:-1:8])
        else:
            plots[sp].plot(data[sp:-1:8])

        plots[sp].set(ylabel=axes[sp+1], xlabel=axes[-1])
    plt.show()
    return None


def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--plot_facets', default=-1, type=int, help="No of facets"
                                                                    "to plot")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--transient_length', default=8192, type=int, help='transient length')
    parser.add_argument("--data_file", default="./shot_data", type=str, help="Name of"
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
