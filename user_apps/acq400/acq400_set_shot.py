#!/usr/bin/env python

"""set shot number of all uuts
"""

import acq400_hapi
import os
import argparse


def run_commands(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    for uut in uuts:
        uut.s1.shot = args.shot

def get_parser():
    parser = argparse.ArgumentParser(description='set shot number of all uuts')
    parser.add_argument('--shot', type=int, default=0)
    parser.add_argument('uuts', nargs='+', help='uut1 [uut2..]')
    return parser

# execution starts here
if __name__ == '__main__':
    run_commands(get_parser().parse_args())




