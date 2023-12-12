#!/usr/bin/env python

"""Arm uuts"""

import acq400_hapi
import os
import argparse

def run_main(args):
    uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]
    for u in uuts:
        u.s0.set_arm = 1

def get_parser():
    parser = argparse.ArgumentParser(description='Set uuts to arm')
    parser.add_argument('uut', nargs='+', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())


