#!/bin/python
'''
plot1.py : plot a long single-channel data file
'''

import numpy as np
import matplotlib.pyplot as plt
import argparse
import scipy.interpolate

MAXSAM = 1000000

def plot_data(args):
    datafile = args.file[0]
    y = np.fromfile(datafile, dtype=args.np_data_type)
    fsegs = datafile.split('.')
    datafile2 = ''.join(fsegs[0:len(fsegs)-1]) + '-up{}'.format(1/args.interval) + fsegs[len(fsegs)-1]
    print("Data file {}, {} samples".format(datafile, len(y)))
    x = np.arange(0, len(y))
    f = scipy.interpolate.interp1d(x, y)
    x2 = np.arange(0, len(y)-1, args.interval)
    print(len(x))
    print(len(x2))
    print(x[len(x)-2:])
    print(x2[len(x2)-10:])
    y2 = f(x2)
    print("Upsample file {}, {} {} samples".format(datafile2, args.interval, len(y2)))
    y2.astype(args.np_data_type).tofile(datafile2)
    if len(y2) > MAXSAM:
        y2 = y2[0:MAXSAM]
        print("Trim to {} for plot".format(len(y2)))
    plt.plot(y2)
    plt.show()


def run_main():
    parser = argparse.ArgumentParser(description='plots a single channel data file')
    parser.add_argument('file', nargs=1, help='data file')
    parser.add_argument('--wordsize', type=int, default=16, help='16 or 32')
    parser.add_argument('--interval', type=float, default=0.2, help='new interval size')
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

