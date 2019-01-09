#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import argparse
import time
import subprocess
try:
    import pyepics
except Exception:
    print "Not importing pyepics."

def stripchart(args):

    plt.ion()
    dlist = []
    for item in range(0, args.chs):
        dlist.append([])

    while True:
        data = subprocess.check_output(["./dumpshm.ai"])
        data = data.replace(" ", "")
        data = data.split(",")
        data = data[:-1]
        print "data = ", data

        for num, list in enumerate(dlist):
            dlist[num].append(data[num])

        for num, list in enumerate(dlist):
            plt.plot(dlist[num])

        if len(dlist[0]) > 75:
            for num, list in enumerate(dlist):
                dlist[num] = dlist[num][1:-1]

        plt.draw()
        plt.pause(0.1)
        plt.clf()
        time.sleep(args.sleep)

def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    parser.add_argument('--sleep', default=1, type=int, help="How long to sleep between stripchart loads")
    parser.add_argument('--chs', default=4, type=int, help="How many channels to plot.")
    args = parser.parse_args()
    stripchart(args)

if __name__ == '__main__':
    run_main()
