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
        uuts.append(acq400_hapi.factory(uut))

    for uut in uuts:
        uut.s0.streamtonowhered = 'stop'

def get_parser():
    parser = argparse.ArgumentParser(description='Stop stream to nowhere')
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())
