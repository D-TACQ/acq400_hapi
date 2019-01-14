#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import argparse

def run_test(args):

    # Load files
    ch1 = np.fromfile(args.file1, dtype=np.int16)
    ch2 = np.fromfile(args.file2, dtype=np.int16)

    x1 = ch1
    x2 = ch2

    # Remove offsets
    x1 = x1 - np.mean(x1);
    x2 = x2 - np.mean(x2);

    # Scale x2 to match x1
    m1 = np.mean(abs(x1))
    x2 = x2 * (m1/np.mean(abs(x2)))

    #Difference
    y3 = (x2 - x1) / m1
    y3_mean = np.mean(abs(np.subtract(x2,x1)) / m1)

    print "Phase difference in rads = ", y3_mean

def run_main():
    parser = argparse.ArgumentParser(description = 'awg speed test')
    parser.add_argument('--file1', type=str, default="CH01", help='ch1 file name')
    parser.add_argument('--file2', type=str, default="CH02", help='ch2 file name')
    run_test(parser.parse_args())


if __name__ == '__main__':
    run_main()
