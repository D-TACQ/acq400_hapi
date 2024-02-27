#!/usr/bin/env python3

"""reunites pre/post channels of 4CH acq480

Data Format
    pre/post
CH1=CH1/CH3
CH2=CH2/CH4
CH3=CH3/CH1
CH4=CH4/CH2

Examples::

    #to plot, fix and save from uut
    ./user_apps/special/acq480_4CH_reuniter.py --plot=0 --save=corrected_data acq1001_301
    #to fix from dir
    ../user_apps/special/acq480_4CH_reuniter.py --src=bad_data --save=good_data acq1001_301

"""

import argparse
import numpy as np
import os
from acq400_hapi import factory, pv
from matplotlib import pyplot as plt

def run_main(args):
    args.channels = 4
    args.type = np.int16

    split_data = []
    if not args.src:
        split_data = data_from_uut(args)
    else:
        split_data = data_from_file(args)

    data = [np.zeros(args.pre + args.post, dtype=args.type) for _ in split_data]

    for idx, arr in enumerate(split_data):
        offset = cyclic_offset(idx + 2)

        if args.nofix:
            data[idx] = arr
            continue

        data[idx][:args.pre] = arr[:args.pre]
        data[offset][args.pre:] = arr[args.pre:]

    if args.plot != None:
        print(f"Plotting data")
        for idx, dat in enumerate(data):
            if args.remove_es and idx in [2,3]:
                dat = np.delete(dat, [args.pre, args.pre + 1])

            if 0 in args.plot or idx + 1 in args.plot:
                plt.plot(dat, label=f"CH{idx + 1}")
        plt.legend()
        plt.show()

    if args.save:
        print(f"Saving data to {args.save}")
        if not os.path.isdir(args.save):
            os.mkdir(args.save)
        for idx, data_arr in enumerate(data):
            filename = os.path.join(args.save, f"{args.uut}_CH{idx + 1:02}")
            with open(filename, 'wb') as fp:
                data_arr.tofile(fp)

def cyclic_offset(num, max_value=3):
    return num % (max_value + 1)

def data_from_uut(args):
    print(f"Reading data from {args.uut}")
    split_data = []
    uut = factory(args.uut)
    args.pre = int(pv(uut.s0.TRANS_ACT_PRE))
    args.post = int(pv(uut.s0.TRANS_ACT_POST))
    args.type = np.int32 if uut.s0.data32 == '1' else np.int16
    for num in range(args.channels):
        split_data.append(uut.read_channels( num + 1 )[0])
    return split_data

def data_from_file(args):
    print(f"Reading data from {args.src}")
    split_data = []
    for num in range(args.channels):
        filepath = os.path.join(args.src, f"{args.uut}_CH0{num + 1}")
        split_data.append(np.fromfile(filepath, dtype=args.type))
    return split_data

def list_of_values(arg):
    return [ int(u) if u.isnumeric() else u for u in arg.split(',') ]

def get_parser():
    parser = argparse.ArgumentParser(description='reunites pre/post channels of 4CH acq480')
    parser.add_argument('--remove_es', default=1, type=int, help="Remove es error")
    parser.add_argument('--nofix', default=0, type=int, help="Do not fix")
    parser.add_argument('--plot', default=None, type=list_of_values, help="Plot data 0 for all or 1,2,3,4")
    parser.add_argument('--save', default=None, help="dir to save resolved data ")
    parser.add_argument('--src', default=None, help="dir to read data from")
    parser.add_argument('--pre', default=50000, type=int, help="pre samples")
    parser.add_argument('--post', default=50000, type=int, help="post samples")

    parser.add_argument('uut', help="uut hostname")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())