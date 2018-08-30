#!/usr/bin/python
"""
UUT is running in Burst/RTM, eg at 50Hz.
Stream the data to host, then 
- pick out all the Start Of Burst ES, then store the next sample
- program plots time series for channel 1

Capture data example:

nc acq1001_343 4210 | pv > burst32-50Hz-512-3.bin

[pgm@harlosh RGM]$ hexdump -e '32/4 "%08x," "\n"' burst32-50Hz-512-3.bin | cut -d, -f1-8 | grep -n aa55f154 | head
425:aa55f154,aa55f154,aa55f154,aa55f154,00000001,00000001,000002a0,000002a0
940:aa55f154,aa55f154,aa55f154,aa55f154,00000002,00000002,000005c0,000005c0
1455:aa55f154,aa55f154,aa55f154,aa55f154,00000003,00000003,000008e0,000008e0
1970:aa55f154,aa55f154,aa55f154,aa55f154,00000004,00000004,00000c00,00000c00
2485:aa55f154,aa55f154,aa55f154,aa55f154,00000005,00000005,00000f20,00000f20
3000:aa55f154,aa55f154,aa55f154,aa55f154,00000006,00000006,00001240,00001240

"""
import numpy as np
import matplotlib.pyplot as plt
import argparse

def raw2volts(xx):
    return float(xx/256 * 10.0 / 0x1000000)

def plot_data(args):
    fname = args.data[0]
    # int32's are easier for math, uint's easier for ES detect.
    # wasting memory keeping a copy, but, memory is cheap..
    rawi = np.fromfile(fname, dtype=np.int32)
    rawu = np.fromfile(fname, dtype=np.uint32)
    ll = len(rawi)/args.nchan
    lltrunc = ll * args.nchan
    chxi = np.reshape(rawi[0:lltrunc], (ll, args.nchan))
    chxu = np.reshape(rawu[0:lltrunc], (ll, args.nchan))
    # extract the first sample in each burst. Approx ll/rtm_translen, ll is safe ..
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

