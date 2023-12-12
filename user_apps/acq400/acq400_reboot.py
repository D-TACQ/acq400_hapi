#!/usr/bin/env python

"""Reboot acq400 systems"""

import acq400_hapi
import argparse

def run_main(args):
    for uutname in args.uuts:
        uut = acq400_hapi.factory(uutname)
        uut.s0.reboot = "3210"

def get_parser():
    parser = argparse.ArgumentParser(description='reboot uuts')
    parser.add_argument('uuts', nargs='+', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
