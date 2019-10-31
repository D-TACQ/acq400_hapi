#!/usr/bin/env python


"""
Example usage:

python3 acq400_pre_post.py --data_test=1 --pre=50000 --post=100000 \
--trg=ext --loops=5 acq1001_084
"""


import acq400_hapi
import argparse
import numpy as np
from acq400_configure_transient import configure_shot
import argparse
import matplotlib.pyplot as plt

def run_shot(args):
    data = []
    configure_shot(args)
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for loop in range(0, args.loops):

        for uut in reversed(uuts):
            uut.s0.transient = "DEMUX = 1"
            uut.s0.set_arm
            uut.statmon.wait_armed()

        for uut in uuts:
            uut.statmon.wait_stopped()
            data.append(uut.read_channels((1)))

        if args.data_test == 1:

            # for ch in data[0]:
            ch = data[0][0]
            zero_crossings = np.where(np.diff(np.sign(ch)))[0]
            test_range = range(args.pre - 5, args.pre + 5)
            for crossing in test_range:
                if crossing in zero_crossings:
                    print("Test passed - pre/post appears to be working.")
                    break
                elif crossing != test_range[-1]:
                    continue
                else:
                    print("Test failed")
                    plt.plot(ch)
                    plt.show()

    return None


def main():
    parser = argparse.ArgumentParser(description='run pre-post capture.')
    acq400_hapi.Acq400UI.add_args(parser)
    parser.add_argument('--data_test', type=int, default=0,
    help='Whether to test the data for the trigger at the pre/post crossover')
    parser.add_argument('--loops', type=int, default=1,
    help='The number of pre-post captures to run.')
    parser.add_argument('uuts', nargs='+', help='uut1 [uut2..]')
    run_shot(parser.parse_args())


if __name__ == '__main__':
    main()
