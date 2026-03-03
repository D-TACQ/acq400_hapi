#!/usr/bin/env python3

"""
Command-line script to set a knobs value on a UUT site.

Arguments:
    <UUT>   : UUT hostname or IP
    <SITE>  : Site number
    <KNOB>  : knob name and value

Example:
    acq400_get_site.py acq2106_000 0 spad 1,8,0
"""

import argparse
import acq400_hapi

def run_main(args):
    uut = acq400_hapi.factory(args.uutname)
    print(uut[args.site].sr(' '.join(args.knob)))

def get_parser():
    parser = argparse.ArgumentParser(description='set the value of a knob')
    parser.add_argument('uutname', help="uut hostname")
    parser.add_argument('site', type=int, help="site number")
    parser.add_argument('knob', nargs=argparse.REMAINDER, help="knob name and value")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
