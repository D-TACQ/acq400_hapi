#!/usr/bin/env python

"""
rawplot : plots raw data
"""

import argparse
import numpy as np
import os
import matplotlib.pyplot as plt

def get_word_type(wtype):
    if wtype == 'int16':
        return np.int16
    elif wtype == 'int32':
        return np.int32
    else:
        print("ERROR, undefined word type {}".format(wtype))
        exit(1)


def plot(args, chx):
    for ch in range(0, args.pchan):
        plt.plot(chx[:,ch])
    plt.title("channels extracted from raw {}".format(args.binfiles[0]))
    plt.show()
    
def load_and_plot(args):
    print("load_and_plot")
    raw = np.fromfile(args.binfiles[0], get_word_type(args.word))
    rc = (np.shape(raw)[0]//args.nchan, args.nchan)
    chx = np.reshape(raw[:rc[0]*rc[1]], rc)
    plot(args, chx)
    
def get_parser():
    parser = argparse.ArgumentParser(description='rawplot')
    parser.add_argument('--nchan', default=1, type=int, help="number of channels")
    parser.add_argument('--pchan', default=1, type=int, help="number of channels to plot")
    parser.add_argument('--word', default='int16', help="int16|int32")
    parser.add_argument('binfiles', nargs='+', help="file[s] to convert")
    return parser
    
# execution starts here

if __name__ == '__main__':
    load_and_plot(get_parser().parse_args())
