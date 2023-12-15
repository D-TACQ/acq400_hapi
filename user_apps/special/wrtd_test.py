#!/usr/bin/env -S python -u

"""tests wrtd functionality.

In particular, find minimum save DELTA_NS
export UUTS="acq2106_182 acq2106_180 acq2106_181 acq2106_172"
"""

import acq400_hapi
from acq400_hapi import intSIAction
from acq400_hapi import intSI
import argparse
import time
import re


def wrtd_test(args):
    args.uuts = [ acq400_hapi.Acq2106(u, has_comms=False, has_wr=True) for u in args.uut ]
    args.master = args.uuts[0]


    args.master.s0.WR_TRG = "OFF"
    args.master.cC.WRTD_TX = '1'
    args.master.cC.WRTD_DELTA_NS = args.wrtd_delta_ns
    args.master.cC.wrtd_commit_tx ='1'


    for u in args.uuts:
        if args.wrtd_txi:
            u.cC.WRTD_TX = '0'
            u.cC.wrtd_commit_tx = '1'
        u.cC.WR_TS_RESET = '1'
        u.cC.WR_WRTT0_RESET = '1'

    try:
        time.sleep(1)
        if not args.wrtd_txi:
            args.master.s0.WR_TRG = "ON"
            for tick in range(0, args.sleep*2):
                time.sleep(0.5)
                if args.verbose == 2:
                    for u in args.uuts:
                        print("{} {}".format(u.uut, u.cC.WRTD_REPORT))
                        
            args.master.s0.WR_TRG = "OFF"
            ts_count = int(args.master.cC.WR_TS_COUNT.split(" ")[1])
        else:
            ts_count = 0
            for tick in range(0, args.sleep):
                args.master.cC.wrtd_txi = args.wrtd_txi
                if args.verbose ==1:
                    print("{}".format('|' if (tick+1)%10==0 else '.'), end='\n' if (tick+1)%50 == 0 or tick==args.sleep-1 else '', flush=True)
                ts_count += 1
                time.sleep(1)
                if args.verbose == 2:
                    for u in args.uuts:
                        print("{} {}".format(u.uut, u.cC.WRTD_REPORT))

    except KeyboardInterrupt:
        if not args.wrtd_txi:
            args.master.s0.WR_TRG = "OFF"
            ts_count = int(args.master.cC.WR_TS_COUNT.split(" ")[1])
        print("aborted by user")

    for u in args.uuts:
        wrtt0_count = int(u.cC.WR_WRTT0_COUNT.split(" ")[1])
        print("{} WRTT0 {}/{} {}".format(u.uut, wrtt0_count, ts_count, "GOOD" if wrtt0_count==ts_count else "FAIL"))



def get_parser():
    parser = argparse.ArgumentParser(description='wrtd_test')
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    acq400_hapi.ShotControllerUI.add_args(parser)

    parser.add_argument('--verbose', default=0, type=int)
    parser.add_argument('--wrtd_txi', default=None, help="tx immediate ID")
    parser.add_argument('--wrtd_delta_ns', default='50M', action=intSIAction, help="set delay NS")
    parser.add_argument('--sleep', default=10, type=int, help="sleep delay")
    parser.add_argument('uut', nargs='+', help="uuts")
    return parser

# execution starts here

if __name__ == '__main__':
    wrtd_test(get_parser().parse_args())
