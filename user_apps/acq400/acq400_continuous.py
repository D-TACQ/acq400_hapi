#!/usr/bin/env python

"""
control continuous capture, default is to toggle, or use --run=1, --stop=1
"""

import acq400_hapi
import argparse

def run_main(args):
    uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]
    
    for uut in uuts:
        if args.run:
            uut.s0.CONTINUOUS = 'start'
        elif args.stop:
            uut.s0.CONTINUOUS = 'stop'
        else:
            if uut.s0.CONTINUOUS == 'CONTINUOUS start':
                uut.s0.CONTINUOUS = 'stop'
            else:
                uut.s0.CONTINUOUS = 'start'

def get_parser():
    parser = argparse.ArgumentParser(description='Start or stop stream')
    parser.add_argument('-r', '--run',  type=int, help="run continuous")
    parser.add_argument('-s', '--stop', type=int, help="stop continuous")
    parser.add_argument('uut', nargs='+', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
