#!/bin/python
'''
plot1.py : plot a long single-channel data file
'''

import numpy as np
import matplotlib.pyplot as plt
import argparse

MAXSAM = 1000000

def plot_data(args):
    datafile = args.file[0]
    ch01 = np.fromfile(datafile, dtype=args.np_data_type)
    print("Data file {}, {} samples".format(datafile, len(ch01)))
    if len(ch01) > MAXSAM:
        ch01 = ch01[0:MAXSAM]
        print("Trim to {} for plot".format(len(ch01)))
    plt.plot(ch01)
    plt.show()


def run_main():
    parser = argparse.ArgumentParser(description='plots a single channel data file')
    parser.add_argument('file', nargs=1, help='data file')
    parser.add_argument('--wordsize', type=int, default=16, help='16 or 32')
    args = parser.parse_args()
    if args.wordsize == 16:
        args.np_data_type = np.int16
        args.WSIZE = 2
    else:
        args.np_data_type = np.int32
        args.WSIZE = 4

    plot_data(args)


if __name__ == '__main__':
    run_main()

