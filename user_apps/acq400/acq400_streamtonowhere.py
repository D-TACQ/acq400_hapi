#!/usr/bin/env python3

"""
A script that streams N samples using streamtonowhered.
"""

import acq400_hapi
import argparse
import time


def main(args):
    uuts = []
    for uut in args.uuts:
        uuts.append(acq400_hapi.Acq400(uut))

    initial_samples = int(uuts[0].s1.sample_count)

    for uut in reversed(uuts):
        uut.s0.streamtonowhered = 'start'

    while int(uuts[0].s1.sample_count) == initial_samples:
        time.sleep(1)

    streamed_samples = int(uuts[0].s1.sample_count)
    while streamed_samples <= args.samples:
        print("Streamed {} of {} samples".format(streamed_samples, args.samples), end = '\r')
        streamed_samples = int(uuts[0].s1.sample_count)
        time.sleep(1)

    print("\nStream finished.")
    for uut in uuts:
        uut.s0.streamtonowhered = 'stop'


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream to nowhere')

    parser.add_argument('--samples', default=100000, type=int,
    help='The number of samples to stream. Not exact.')

    parser.add_argument('uuts', nargs='+', help="uuts")

    args = parser.parse_args()
    main(args)


if __name__ == '__main__':
    run_main()
