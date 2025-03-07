#!/usr/bin/env python3

import acq400_hapi
import argparse
import sys

from acq400_hapi import timing_ms as timing_ms
from acq400_hapi import timing as timing

# cq : knob command KK=X or query KK

@timing_ms
def cq(uut, site, knob_cq):
    value = uut.svc[f's{site}'].sr(knob_cq)

def iterate(args):
    if args.input is None:
        for opdef in args.knobs:
            yield opdef
    elif args.input == '-':
        for line in sys.stdin:
            yield line.strip();
    else:
        with open(args.input, "r") as file:
            yield file.readline().strip()


def run_main(args):
    uut = acq400_hapi.Acq400(args.uut[0])

    for opdef in iterate(args):    
        site, knob_cq = opdef.split(',')
        print(f'knob_cq {knob_cq}')
        cq(uut, site, knob_cq)

def get_parser():
    parser = argparse.ArgumentParser(description='Instrument knob timing')
    parser.add_argument('--input', default=None, help="input file, '-' is stdin")
    parser.add_argument('uut', nargs=1 )
    parser.add_argument('knobs', nargs='*')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

