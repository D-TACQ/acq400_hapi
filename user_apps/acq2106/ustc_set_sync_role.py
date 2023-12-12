#!/usr/bin/env python

""" 
ustc_sync_role ::: set master slave clocking for ustc stack
"""


import argparse
import acq400_hapi
import time
import sys
if sys.version_info < (3, 0):
    from future import builtins
    from builtins import input


def run_main(args):
    uuts = [ acq400_hapi.Acq2106(addr) for addr in args.uuts ]
    role = "master"

    for uut in uuts:
        sr = '{} {} {}'.format(role, args.fs, args.fclk)
#        print("ustc {} sync_role {} sr {}".format(uut, role, sr))
        uut.s0.sync_role = sr
        role = "slave"

def get_parser():
    parser = argparse.ArgumentParser(description="Sync role ustc stack")
    parser.add_argument("--fs", default='10M', help='sample clock')
    parser.add_argument("--fclk", default='33333000', help='master clock')
    parser.add_argument("uuts", nargs='+', help="uuts m1 [s1 s2 ...]")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
