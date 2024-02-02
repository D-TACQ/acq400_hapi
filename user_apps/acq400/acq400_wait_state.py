#!/usr/bin/env python

"""Blocks until uut(s) reach state(s)

Example::

    ./user_apps/acq400/acq400_wait_state.py --state=ARM acq1001_001
    ./user_apps/acq400/acq400_wait_state.py --state=IDLE --timeout=30 acq1001_001
    ./user_apps/acq400/acq400_wait_state.py --state=RUNPRE,RUNPOST acq1001_001 acq1001_002
    

"""

import acq400_hapi
import argparse
import time

def run_main(args):
    valid_states = ["IDLE", "ARM", "RUNPRE", "RUNPOST", "POPROCESS", "CLEANUP"]
    if not any(val in args.states for val in valid_states):
        exit('Invalid state')
    start_time = time.time()
    uuts = [acq400_hapi.factory(uut) for uut in args.uuts]
    while True:
        for idx, uut in enumerate(uuts):
            state = acq400_hapi.STATE.str(uut.statmon.get_state())
            if state in args.states:
                print(f"{uut.uut} reached {state}")
                uuts.pop(idx)
        if len(uuts) == 0:
            print(f"All states reached")
            exit(0)
        if args.timeout:
            if time.time() - start_time > args.timeout:
                print("Timeout reached")
                exit(1)
        time.sleep(0.2)

def list_of_values_upper(arg):
    return list(map(str.upper, arg.split(',')))

def get_parser():
    parser = argparse.ArgumentParser(description='Blocks until uut(s) reach state(s)')
    parser.add_argument('--states', required=True, type=list_of_values_upper, help="target state")
    parser.add_argument('--timeout', type=int, default=None, help="max wait")
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())