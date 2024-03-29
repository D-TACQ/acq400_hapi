#!/usr/bin/env python

"""configure transient

.. rst-class:: hidden

    configure multiple acq400

    usage: acq400_configure_transient.py [-h] [--pre PRE] [--post POST]
                                    [--clk CLK] [--trg TRG] [--sim SIM]
                                    [--trace TRACE]
                                    uuts [uuts ...]

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


def get_parser(argStr=None):
    parser = argparse.ArgumentParser(description='Configure transient on multiple uuts')
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    parser.add_argument('uuts', nargs='+', help="uut pairs: m1,m2 [s1,s2 ...]")
    return parser


def run_main(args):
    configure_shot(args, [acq400_hapi.Acq400(u) for u in args.uuts])


if __name__ == '__main__':
    run_main(get_parser().parse_args())
