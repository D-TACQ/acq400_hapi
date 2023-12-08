#!/usr/bin/env python


"""A script to loop pre-post captures.

A data_test can also be run, where the system will assume a slow free running
trigger is given (~0.5Hz) with CH01 sampling a square wave.

Example usage::

    python3 acq400_pre_post.py --data_test=1 --pre=50000 --post=100000 \
    --trg=ext --shots=5 acq1001_084
"""


import acq400_hapi
import argparse
import numpy as np
# from acq400_configure_transient import configure_shot
from . import acq400_configure_transient
import argparse
import matplotlib.pyplot as plt
import sync_role


def validate(args, data, shot):
# for ch in data[0]:
    ch = data[0][0]
    zero_crossings = np.where(np.diff(np.sign(ch)))[0]
    test_range = range(args.pre - 5, args.pre + 5)

    for crossing in test_range:
        if crossing in zero_crossings:
            print("{} Test passed - pre/post appears to be working.".format(shot))
            break
        elif crossing != test_range[-1]:
            continue
        else:
            print("{} Test failed".format(shot))
            plt.plot(ch)
            plt.show()

def configure_shot(args):
    acq400_configure_transient.configure_shot(args)
    sync_role.run_shot(args)
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for uut in uuts:
        uut.s0.transient = "DEMUX=1"

    return uuts

def run_shot(args, uuts, shot):
    for uut in reversed(uuts):
        uut.s0.set_arm
        uut.statmon.wait_armed()
    data = []

    for uut in uuts:
        uut.statmon.wait_stopped()
        data.append(uut.read_channels((1)))

    if args.data_test == 1:
        validate(args, data, shot)


def run_shots(args, uuts):
    for shot in range(0, args.shots):
        run_shot(args, uuts, shot)



def main(args):
    run_shots(args, configure_shot(args))

def get_parser():
    parser = argparse.ArgumentParser(description='config pre-post then capture')
    acq400_hapi.Acq400UI.add_args(parser)
    parser.add_argument('--data_test', type=int, default=0,
                        help='Whether to test the data for the trigger at the pre/post crossover')
    parser.add_argument('--shots', type=int, default=1,
                        help='The number of pre-post captures to run.')

    parser.add_argument('--enable_trigger', default=None, help="set this to enable the trigger all other args ignored")
    parser.add_argument('--toprole', default='master', help="role of top in stack")
    parser.add_argument('--fclk', default='1000000', help="sample clock rate")
    parser.add_argument('--fin',  default='1000000', help="external clock rate")
    parser.add_argument('--clkdiv', default=None, help="optional clockdiv")

    parser.add_argument('uuts', nargs='+', help='uut1 [uut2..]')
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())