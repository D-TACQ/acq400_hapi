#!/usr/bin/env python

""" configure transient 
    acq1014_configure_transient UUT1 UUT2 [NPOST] [trigger=int|ext|ext2]
"""

import sys
import acq400_hapi
import argparse
import sets
from acq400_hapi import intSI as intSI

def configure_shot(args):
    if len(args.uuts)%2:
        print("ERROR: must be an even number of uuts, minimum 2")
        sys.exit(1)

    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]    
    mset = sets.Set(uuts[0:2])
    pre = intSI(args.pre)
    post = intSI(args.post)
    t_args = [args.trg.split(' ')[0], 
              "prepost" if pre>0 else "post", 
              "falling" if "falling" in args.trg else "rising"]    
    c_args = args.clk.split(' ')
    if len(c_args) > 1:
        c_args[1] = intSI(c_args[1])
        if len(c_args) > 2:
            c_args[2] = intSI(c_args[2])
    c_args = [str(x) for x in c_args]

    for u in uuts:
        print("uut:%s" % u.uut)
        u.s0.trace = 1
        u.s0.set_abort = 1;
        u.s0.transient = "PRE=%d POST=%d SOFT_TRIGGER=0" % (pre, post)

        u.s0.acq1014_select_trg_src = ' '.join(t_args)
        u.s0.acq1014_select_clk_src = ' '.join(c_args)

        u.s0.trace = 0

def run_main():
    parser = argparse.ArgumentParser(description='configure multiple acq1014')
    parser.add_argument('--pre', default=0, help="pre trigger length")
    parser.add_argument('--post', default=100000, help="post trigger length")
    parser.add_argument('--clk', default="int 80000000", help='clk "int|ext SR [CR]"')
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('uuts', nargs='*', help="uut pairs: m1,m2 [s1,s2 ...]")
    configure_shot(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()

