#!/usr/bin/python
# make_waves --nchan --nsam .. make rainbow patterns
# todo add padto option to pad non-binary WF to binary buffer
# todo handle int32 data

import numpy as np
import argparse
import acq400_hapi
from acq400_hapi import intSIAction


def write_out(args, aw):
    fn = "rainbow-{}-{}-{}".format(args.fname[0], args.nchan, args.nsam)
    (aw*(2**15-1)).astype(np.int16).tofile(fn)

def make_waves(args):
    sin = np.sin(np.array(list(range(args.nsam))) * args.cycles*2*np.pi/args.nsam)
    aw = np.zeros((args.nsam, args.nchan))
    for ch in range(0, args.nchan):
        aw[:,ch] = -1.0 + 2.0*ch/args.nchan
    write_out(args, aw)

def run_main():
    parser = argparse.ArgumentParser(description='create host site multi-channel AWG file')
    parser.add_argument('--nchan', type=int, default=32)
    parser.add_argument('--nsam', action=intSIAction, decimal=False, default=0x1000, help='number of samples, can suffix M for binary mega')
    parser.add_argument('--cycles', type=int, default=10, help='number of cycles in waveform')
    parser.add_argument('--padto', action=intSIAction, decimal=False, default=0, help='number of samples, can suffix M for binary mega')
    parser.add_argument('fname', nargs=1, help='file name root')
    args = parser.parse_args()
    if args.padto > 0:
        print("WORKTODO: padto option NOT implemented")
    make_waves(args)

if __name__ == '__main__':
    run_main()

