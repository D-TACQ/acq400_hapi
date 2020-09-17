#!/usr/bin/env python

"""
configure transient
acq1014_configure_transient UUT1 UUT2 [NPOST] [trigger=int|ext|ext2]

usage: acq400_configure_transient.py [-h] [--pre PRE] [--post POST]
                                 [--clk CLK] [--trg TRG] [--sim SIM]
                                 [--trace TRACE]
                                 uuts [uuts ...]

configure multiple acq400

positional arguments:
  uuts           uut pairs: m1,m2 [s1,s2 ...]

optional arguments:
  -h, --help     show this help message and exit
  --pre PRE      pre-trigger samples
  --post POST    post-trigger samples
  --clk CLK      int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG      int|ext,rising|falling
  --sim SIM      nosim|s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE  1 : enable command tracing
"""

import sys
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse


def configure_shot(args, uuts):
    for uut in uuts:
        if hasattr(uut.s0, 'TIM_CTRL_LOCK'):
            print("LOCKDOWN {}".format(uut))
            uut.s0.TIM_CTRL_LOCK = 0
        acq400_hapi.Acq400UI.exec_args(uut, args)


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='configure multiple acq400')
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    parser.add_argument('uuts', nargs='+', help="uut pairs: m1,m2 [s1,s2 ...]")
    return parser.parse_args(argStr)


def run_main():
    args = get_args()
    configure_shot(args, [acq400_hapi.Acq400(u) for u in args.uuts])


# execution starts here

if __name__ == '__main__':
    run_main()
