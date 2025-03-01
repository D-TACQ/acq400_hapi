#!/usr/bin/env python3

import acq400_hapi
import argparse

from acq400_hapi import timing as timing


print("hello world")

@timing
def exec_query(knob):
    pass

@timing
def exec_set(knob, value):
    pass

def run_main(args):
    print(f'uut {args.uut}')
    uut = acq400_hapi.Acq400(args.uut[0])

    for sk in args.knobs:
        site, knob = sk.split(',')
        print(f'site:{site} knob:{knob}')

def get_parser():
    parser = argparse.ArgumentParser(description='Instrument knob timing')
    parser.add_argument('uut', nargs=1 )
    parser.add_argument('knobs', nargs='+')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

