#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import argparse

def raw2volts(xx):
    return float(xx/256 * 10.0 / 0x1000000)

def plot_data(args):
    fname = args.data[0]
    rawi = np.fromfile(fname, dtype=np.int32)
    rawu = np.fromfile(fname, dtype=np.uint32)
    ll = len(rawi)/args.nchan
    chxi = np.reshape(rawi, (ll, args.nchan))
    chxu = np.reshape(rawu, (ll, args.nchan))
    chx = np.zeros((args.nchan, ll))
    ss = 0
    for ii in range(0, ll):
        if chxu[ii][0] == 0xaa55f154 and chxu[ii][1] == 0xaa55f154:
            for cc in range(0, args.nchan):
                chx[cc][ss] = raw2volts(chxi[ii+1][cc])
            ss += 1
            if ss < 10:
                print("{}, {}".format(ii, raw2volts(chxi[ii+1][0])))

    print("number of samples: {}".format(ss))
    plt.plot(chx[0][0:ss])
    plt.show()



def run_main():
    parser = argparse.ArgumentParser(description='rgm plot demo')
    parser.add_argument('--nchan', type=int, default=32)
    parser.add_argument('data', nargs=1, help="data ")
    plot_data(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()

