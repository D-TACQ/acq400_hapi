#!/usr/bin/env python3

"""
Read data from 0:SLOWMON:MEAN then plot and save

Usage:
    ./user_apps/pyepics/slowmon_archiver.py  acq2106_007 --runtime=60 --pchan=1-5,161 --ptime=1
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
import epics
import time
import os

class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    def __missing__(self, attr):
        self.setdefault(attr, DotDict())
        return self[attr]

dataset = DotDict()

def run_main(args):

    # Setup
    timestamp = time.strftime("%y-%m-%d_%H-%M-%S")

    for uut in args.uuts:

        ms = epics.caget(f"{uut}:0:SLOWMON:SLOWMONMS")
        if not ms: return

        rate = 1 / (ms / 1000)
        samplelen = len(epics.caget((f"{uut}:0:SLOWMON:MEAN")))
        datalen = int(rate * samplelen * args.runtime)

        dataset[uut].cursor =       0
        dataset[uut].ms =           ms
        dataset[uut].samplelen =    samplelen
        dataset[uut].datalen =      datalen
        dataset[uut].data =         np.empty(datalen, dtype=np.float32)
        dataset[uut].pv =           epics.PV(f"{uut}:0:SLOWMON:MEAN")

    for uut in dataset:
        dataset[uut].pv.add_callback(callback)

    # Wait and print status
    try:
        t0 = time.time()
        while True:
            t1 = time.time() - t0
            print(f"\n{t1:.0f}/{args.runtime}s")
            for uut in dataset:
                print(f"{uut} {dataset[uut].cursor * 4}/{dataset[uut].datalen * 4} Bytes")
            if t1 > args.runtime: break
            time.sleep(1)
    except KeyboardInterrupt: 
        print("Stopping")

    # Plotting and Saving
    for uut in dataset:
        dataset[uut].pv.clear_callbacks()
        
        plt.figure(f"{uut}_SLOWMON_MEAN", figsize=(10, 4))
        plt.title(f"{uut}:0:SLOWMON:MEAN {args.runtime}s {dataset[uut].ms}ms Chans {args.pchans}")

        chanlen = len(dataset[uut].data[0::dataset[uut].samplelen])
        time_base = np.linspace(0, args.runtime, chanlen) if args.ptime else np.arange(chanlen)

        for chan in args.pchans:
            plt.plot(time_base, dataset[uut].data[chan - 1::dataset[uut].samplelen], label=f"CH {chan}")
        plt.legend()
        plt.xlabel('Time (s)') if args.ptime else plt.xlabel('Samples')
        plt.ylabel('Volts (V)')

        if args.save > 0:
            filename = f"{uut}.{timestamp}.CH{dataset[uut].samplelen}.{dataset[uut].ms}ms.{args.runtime}s"
            os.makedirs(args.root, exist_ok=True)
            savepath = os.path.join(args.root, filename + '.dat')
            print(f"{uut} data saved to {savepath}")
            dataset[uut].data.tofile(savepath)

        if args.save == 2: 
            savepath = os.path.join(args.root, filename + '.png')
            print(f"{uut} plot saved to {savepath}")
            plt.savefig(savepath)

    if args.plot: plt.show()

def callback(pvname, value, *args, **kwargs):
    uut = pvname.split(':')[0]
    samplelen = len(value)
    start = dataset[uut].cursor
    if cursor >= dataset[uut].datalen:
        return
    finish = start + samplelen
    dataset[uut].data[start:finish] = value
    dataset[uut].cursor = finish

def list_of_channels(arg):
    channels = []
    for chan in arg.split(','):
        if '-' in chan:
            chan = list(map(int, chan.split('-')))
            channels.extend(list(range(chan[0], chan[1] + 1)))
            continue
        channels.append(int(chan))
    return channels

def get_parser():
    parser = argparse.ArgumentParser(description='Read data from 0:SLOWMON:MEAN then plot and save')
    parser.add_argument('--pchans', default='1', type=list_of_channels, help="Channels to plot 1,2,3-5 [default=1]")
    parser.add_argument('--ptime', default=1, type=int, help="Plot time (no: 0) or (yes: 1) [default]")
    parser.add_argument('--runtime', default=60, type=int, help="Total seconds of data to capture [default=60]")
    parser.add_argument('--save', default=1, type=int, help="(don't save: 0), (save data: 1)[default] or (save data and plot: 2)")
    parser.add_argument('--root', default="slowmon_data", help="Save data dir")
    parser.add_argument('--plot', default=1, type=int, help="(don't plot: 0) or (plot: 1) [default]")
    parser.add_argument('uuts', nargs='+', help="uut hostnames")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

