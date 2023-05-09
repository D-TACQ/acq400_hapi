#!/usr/bin/env python3

import argparse
import acq400_hapi
import time
import numpy as np
from matplotlib import pyplot as plt
from prettytable import PrettyTable

"""
Usage:
    ./test_apps/slowmon_validator.py acq2106_388
    ./test_apps/slowmon_validator.py --chan=2 --fs=1,33,66 --clk=1M,2M,3M acq2106_388
"""

def run_main(args):
    clk_values = ['10M', '20M', '40M',]
    slowmon_fs = [1, 45, 65, 85]
    if args.fs :
        slowmon_fs = args.fs.split(',')
    if args.clk :
        clk_values = args.clk.split(',')

    print(f"Clk {*clk_values,}")
    print(f"Fs {*slowmon_fs,}")
    uut = acq400_hapi.factory(args.uut)
    signal_chan = args.chan - 1

    for clk in clk_values:
        print(f"Clk: {clk} Channel: {args.chan}")
        uut.s0.CONTINUOUS = 0
        uut.s0.sync_role = f"master {clk}"
        uut.s0.CONTINUOUS = 1
        plt.figure(1)
        t = PrettyTable(['fs', 'wavelength (samples)', 'Sps', 'Error'])
        t.title = f"{args.uut} Clk {clk}"
        values = {}
        for fs in slowmon_fs:

            print(f"slowmon_fs {fs}")
            uut.s0.SLOWMON_FS = fs
            fskey = f"fs{fs}"
            values[fskey] = []
            edge_idxs = []
            last = None
            start_time = time.time()

            for idx, (chx, spx) in enumerate(uut.stream_slowmon()):
                values[fskey].append(chx[signal_chan])
                current = np.sign(chx[signal_chan])
                if not last:
                    last = current

                if current != last:
                    if args.debug:
                        print(f"Waveform crossed zero at idx: {idx} value: {chx[signal_chan]}")
                    last = current
                    if len(edge_idxs) > 0 and idx - edge_idxs[-1] < args.cross_threshold:
                        if args.debug:
                            print('cross below threshold ignoring')
                    else:
                        edge_idxs.append(idx)

                if len(edge_idxs) >= 3:
                    diff = edge_idxs[2] - edge_idxs[0]
                    time_taken = time.time() - start_time
                    if args.debug:
                        print(f"time taken: {time_taken} total samples: {idx}")
                    sps = round((idx + 1) / time_taken, 1)
                    if diff > 50:
                        t.add_row([fskey, diff, sps, ''])
                        break
                    t.add_row([fskey, diff, sps, 'Error'])
                    break

            if args.plot:
                plt.plot(values[fskey], label=fskey)

        print(t)
        if args.save:
            filename = f"{args.uut}_{clk}.csv"
            with open(filename, 'w', newline='') as file:
                file.write(t.get_csv_string())
        if args.plot:
            plt.title(f"{args.uut} Clk {clk}")
            plt.legend()
            plt.show()

def get_parser():
    parser = argparse.ArgumentParser(description='slowmon validator')
    parser.add_argument('--plot', type=int, default=1, help='to plot or not to plot')
    parser.add_argument('--chan', type=int, default=1, help='Channel to check')
    parser.add_argument('--save', type=int, default=1, help='Save results to csv')
    parser.add_argument('--fs', default=None, help='fs values to use e.g. 1,50,99')
    parser.add_argument('--clk', default=None, help='clk_sync values to use e.g. 10M,20M,50M')
    parser.add_argument('--cross_threshold', default=10, type=int, help='number of samples before cross is valid')
    parser.add_argument('--debug', default=0, type=int, help='enable debugging')
    parser.add_argument('uut', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())