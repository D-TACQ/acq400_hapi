#!/usr/bin/env python

"""uut abort"""

import acq400_hapi
import os
import argparse
import threading
import time

def abort_action(u):
    def _abort_action():
        u.s0.TIM_CTRL_LOCK = 0
        u.s0.TRANSIENT_SET_ABORT = '1'
        time.sleep(2)
        u.s0.streamtonowhered = 'stop'
        u.s0.set_abort = 1

        try:
            u.s1.AWG_MODE_ABO = '1'
            u.s1.AWG_MODE_ABO = '0'
        except:
            pass
    return _abort_action

def run_main(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uut ]

    for u in uuts:
        thx = [ threading.Thread(target=abort_action(u)) for u in uuts ]
        for t in thx:
            t.start()
        for t in thx:
            t.join()

def get_parser():
    parser = argparse.ArgumentParser(description='configure acq400_abort')
    parser.add_argument('uut', nargs='+', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())