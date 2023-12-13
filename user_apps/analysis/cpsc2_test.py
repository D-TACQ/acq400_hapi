#!/usr/bin/env python


"""
This is a script used to analyse CPSC2 data.

Example usage::

    python3.6 cpsc2_test.py --data /home/sean/PROJECTS/workspace/cpsc2_data/small/bigrawlogfile2 --zoom 36000 36500

"""

import sys
#if sys.version_info < (3, 0):
#    from __future__ import print_function
#    from future import builtins
import argparse
import numpy as np
import matplotlib.pyplot as plt


def get_data(args):
    data = np.fromfile(args.data, dtype=np.int32)
    # reshape the data to be an 64 x N matrix where i is 64 and j is N in
    # traditional matrix nomenclature. This means channels are rows.
    number_of_elements_to_remove = data.size % args.nchan
    if number_of_elements_to_remove != 0:
        data = data[:-number_of_elements_to_remove] # Need to do this to reshape.

    data = data.reshape((-1,args.nchan)).transpose()
    # Now we can access whole channels by doing: data[ch,0:] and access parts
    # of channels by doing: data[ch, index1 : index2]
    return data


def check_counters(data, skip_on_val="disable", skip_on_zero=0, col_name="x"):
    skipped_counter = 0
    last_sample = 0
    for index, sample in enumerate(data):
        if index == 0:
            last_sample = sample
            continue
        if skip_on_zero == 1:
            if sample == 0 or last_sample == 0:
                last_sample = sample
                continue
        if skip_on_val != "disable":
            if sample == skip_on_val:
                skipped_counter += 1
                continue
            if last_sample == skip_on_val:
                last_sample = sample
                continue
        if sample == last_sample + 1:
            last_sample = sample
            continue
        if skipped_counter == 10:
            print("Skipped counter reached 10, resetting now.")
            skipped_counter = 0
        else:
            print("Error found in column: {}".format(col_name))
            print("Sample gap found @ index ", index)
            print("Sample gap: ", sample - last_sample)
            print("Current sample = ", hex(sample), sample)
            print("Last sample = ", hex(last_sample), last_sample)
            print("\n\n")
            last_sample = sample
            # exit()


def analyse_data(data, args):

    sample_counter_col = 49-1
    sfp_seq_num = 33-1
    print("Checking sample counters.")
    check_counters(data[sample_counter_col::args.nchan],
    col_name="sample counter")

    print("Checking SFP seq numbers.")
    check_counters(data[sfp_seq_num::args.nchan],
    skip_on_val=-0x11111112, skip_on_zero=1, col_name="sfp sequence counter")

    return None


def plot_data(data, args):

    zoom = args.zoom
    print("Zoom = ", zoom)
    print(type(zoom[0]))

    if args.zoom[1] == 'data[0].size':
        args.zoom[1] = eval(args.zoom[1])

    f, plots = plt.subplots(5, 1)
   
    for row in [1-1, 2-1, 3-1, 4-1]:
        plots[0].plot(data[row,zoom[0]:zoom[1]])
        plots[0].set_title("CPSC2 data columns 1-4 (AI)")
        plots[0].legend(('01', '02', '03', '04'))
        plots[0].grid(True)

    for row in [33-1, 41-1]:
        # plots[0].plot(data[col::args.nchan])
        plots[1].plot(data[row,zoom[0]:zoom[1]])
        plots[1].set_title("CPSC2 data columns 33, 41")
        plots[1].legend(('33', '41'))
        plots[1].grid(True)

    for row in [34-1, 35-1, 36-1, 37-1]:
        plots[2].plot(data[row,zoom[0]:zoom[1]])
        plots[2].set_title("CPSC2 data columns 34, 35, 36, 37")
        plots[2].legend(('34', '35', '36', '37'))
        plots[2].grid(True)

    for row in [42-1, 43-1, 44-1, 45-1]:
        plots[3].plot(data[row,zoom[0]:zoom[1]])
        plots[3].set_title("CPSC2 data columns 42, 43, 44, 45")
        plots[3].legend(('42', '43', '44', '45'))
        plots[3].grid(True)

    for row in [49-1]:
        plots[4].plot(data[row,zoom[0]:zoom[1]])
        plots[4].set_title("CPSC2 SPAD[0]")
        plots[4].legend(('49'))
        plots[4].grid(True)


    plt.grid(True)
    plt.show()


def analyse_stdin(args):
    try:
        while True:
            # Do stuff here
            data = sys.stdin.read(32*1024*1024) # 32 bytes * 1024^2
            data = np.fromstring(data, dtype=np.int32)
            analyse_data(data, args)
    except KeyboardInterrupt:
        print("Stopping python analysis now.")
        exit(1)
    return None


def run_test(args):
    if args.analyse == 1:

        if args.stdin == 1:
            analyse_stdin(args)
        else:
            data = get_data(args)
            analyse_data(data, args)
    data = get_data(args)
    plot_data(data, args)

#    import code
#    code.interact(local=locals())

    return None


def get_parser():
    parser = argparse.ArgumentParser(description='CPSC2 data validity test.')

    parser.add_argument('--data', default="./cpsc2_002_raw_001.dat",
    type=str, help='Which data file to load.')

    parser.add_argument('--nchan', default=64, type=int,
    help="How many channels in one sample (including SPAD).")

    parser.add_argument('--analyse', default=0, type=int,
    help="Run analysis on the data Default=0.")

    parser.add_argument('--stdin', default=0, type=int,
    help="Pull the data to be analysed from STDIN instead of a file.")

    parser.add_argument('--zoom', default=[0, 'data[0].size'], nargs='+',
    type=int, help="Allows the user to zoom into a portion of the data. To use \
    the user must provide two numbers: --zoom 25000 35000. Default is whole \
    dataset.")
    return parser


if __name__ == '__main__':
    run_test(get_parser().parse_args())


