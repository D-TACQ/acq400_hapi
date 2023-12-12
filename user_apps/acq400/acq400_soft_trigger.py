#!/usr/bin/env python

"""fire a soft trigger

.. rst-class:: hidden
    usage: acq400_soft_trigger.py [-h] uut [uut ...]

    configure fire a soft trigger

    positional arguments:
    uut         uut

    optional arguments:
    -h, --help  show this help message and exit
"""

import acq400_hapi
import os
import argparse
import time

def run_main(args):
    uuts = [ acq400_hapi.Acq400(u) for u in args.uut ]

    if len(uuts) == 1:
        u = uuts[0]
        if args.instrument:
            u.s0.SIG_TRG_MB_RESET = 1
            time.sleep(1)

        it = 0        
        while it < args.count:        
            u.s0.soft_trigger = 1
            if args.interval > 0:
                time.sleep(args.interval)
            it += 1
            
        if args.instrument:
            tcount = u.s0.SIG_TRG_MB_COUNT
            print("{}: sent {} triggers, actual {} triggers ".format("PASS" if tcount == args.count else "FAIL", args.count, tcount))
        
    else:
        print("multiple uuts, send one trigger to each")
        for u in uuts:
            u.s0.soft_trigger = 1
    

def get_parser():
    parser = argparse.ArgumentParser(description='Fire soft trigger on UUT')
    parser.add_argument('--count', type=int, default=1, help="send many triggers, perhaps to test max rate")
    parser.add_argument('--interval', type=float, default=0, help="send periodic trigger (s) default: 0 aka max")
    parser.add_argument('--instrument', type=int, default=0, help="count before and after")
    parser.add_argument('uut', nargs='+', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())