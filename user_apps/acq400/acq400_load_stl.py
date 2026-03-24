#!/usr/bin/env python3

"""
Play STL file via GPG

Usage:

    ./user_apps/acq400/acq400_load_stl.py --stl STL/sos0.stl --mode=0 --trg=1,1,1 acq1102_010
"""

import acq400_hapi
import argparse

def run_main(args):    

    uut = acq400_hapi.factory(args.uutname)

    uut.s0.GPG_ENABLE = 0
    
    uut.s0.gpg_timescaler = args.timescaler
    uut.s0.GPG_MODE = args.mode

    if args.trg:
        print(f"TRG = {args.trg}")
        enabled, signal, sense = args.trg.split(',')
        uut.s0.GPG_TRG = enabled
        uut.s0.GPG_TRG_DX = signal
        uut.s0.GPG_TRG_SENSE = sense

    if args.clk:
        print(f"CLK = {args.clk}")
        enabled, signal, sense = args.clk.split(',')
        uut.s0.GPG_CLK = enabled
        uut.s0.GPG_CLK_DX = signal
        uut.s0.GPG_CLK_SENSE = sense

    uut.s0.SIG_EVENT_SRC_0 = 'GPG'
    uut.s0.SIG_FP_GPIO = 'EVT0'

    with open(args.stl, 'r') as fp:
        uut.load_gpg(fp.read())

    uut.s0.GPG_ENABLE = '1'

def get_parser():
    parser = argparse.ArgumentParser(description='Play STL file via GPG')

    parser.add_argument('--stl', type=str, help='stl file')
    parser.add_argument('--mode', default=0, type=int, help='GPG mode (0=ONCE, 2=LOOP, 3=LOOPWAIT)')
    parser.add_argument('--timescaler', '--ts', default=1, type=int, help="GPG timescaler")
    parser.add_argument('--trg', default=None, help='gpg trg triplet (1,0,0)')
    parser.add_argument('--clk', default=None, help='gpg clk triplet (1,0,0)')

    parser.add_argument('uutname', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())