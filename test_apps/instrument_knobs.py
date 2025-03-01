#!/usr/bin/env python3

import acq400_hapi
import argparse

from acq400_hapi import timing as timing

# knob_cq : knob command KK=X or query KK
@timing
def exec_knob_cq(uut, site, knob_cq):
    value = uut.svc[f's{site}'].sr(knob_cq)
#    print(f'value {value}')

def run_main(args):
    uut = acq400_hapi.Acq400(args.uut[0])
    
    for opdef in args.knobs:
        site, knob_cq = opdef.split(',')
        print(f'knob_cq {knob_cq}')
        exec_knob_cq(uut, site, knob_cq)

def get_parser():
    parser = argparse.ArgumentParser(description='Instrument knob timing')
    parser.add_argument('uut', nargs=1 )
    parser.add_argument('knobs', nargs='+')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

