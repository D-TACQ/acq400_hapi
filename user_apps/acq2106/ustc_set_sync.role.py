#!/usr/bin/env python

""" 
ustc_sync_role ::: set master slave clocking for ustc stack
"""


import argparse
import acq400_hapi
import time
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ustc_set_sync_role")
    parser.add_argument("--fs", default='10M', help='sample clock')
    parser.add_argument("--fclk", default='33333000', help='master clock')
    parser.add_argument("uuts", nargs='+', help="uuts m1 [s1 s2 ...]")
    run_main(parser.parse_args())



