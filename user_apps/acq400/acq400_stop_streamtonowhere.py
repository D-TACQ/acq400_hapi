#!/usr/bin/env python3

"""
A script that stops streamtonowhered.
"""

import acq400_hapi
import argparse
import time


def main(args):
    uuts = []
    for uut in args.uuts:
        uuts.append(acq400_hapi.Acq400(uut))

    for uut in uuts:
        uut.s0.streamtonowhered = 'stop'


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream to nowhere')

    parser.add_argument('uuts', nargs='+', help="uuts")

    args = parser.parse_args()
    main(args)


if __name__ == '__main__':
    run_main()
