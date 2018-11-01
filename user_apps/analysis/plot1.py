#!/bin/python
'''
plot1.py : plot a long single-channel data file
'''

import numpy as np
import matplotlib.pyplot as plt
import argparse

MAXSAM = 1000000

def plot_data(datafile):
    ch01 = np.fromfile(datafile, dtype='int16')
    print("Data file {}, {} samples".format(datafile, len(ch01)))
    if len(ch01) > MAXSAM:
        ch01 = ch01[0:MAXSAM]
        print("Trim to {} for plot".format(len(ch01)))
    plt.plot(ch01)
    plt.show()


def run_main():
    parser = argparse.ArgumentParser(description='plots a single channel data file')
    parser.add_argument('file', nargs=1, help='data file')
    args = parser.parse_args()
    plot_data(args.file[0])


if __name__ == '__main__':
    run_main()

