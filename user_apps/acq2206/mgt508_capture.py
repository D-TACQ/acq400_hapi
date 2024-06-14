#!/usr/bin/env python

"""
control continuous capture, default is to toggle

.. rst-class:: hidden

    positional arguments:
    uut         uut

    optional arguments:
    --run=1 
    --stop=1
    -h, --help  show this help message and exit
"""

import acq400_hapi
import argparse
import time
import subprocess
import threading
from acq400_hapi import timing as timing

def configure_acq(args, acq):
    acq.s1.simulate = args.simulate

GB1 = 0x40000000

def pull(mgt):
    print(f"this is pull {mgt.uut}")
    mgt.pull()

def configure_mgt(args, mgt):
    mgt.set_capture_length(args.GB*0x400)

@timing
def clear_mem(args, mgt):
    result = subprocess.run(['./scripts/mgt508_clear_mem', mgt.uut])
    print(f'Return code : {result.returncode}')

@timing
def read_data(args, mgt):
    if args.simulate:
        result = subprocess.run(['./scripts/mgt508_validate_mem', mgt.uut, str(args.GB)])
    else:
        result = subprocess.run(['./scripts/mgt508_read_mem', mgt.uut, str(args.GB)])
    print(f'Return code : {result.returncode}')

def start_pull(args, mgt):
    args.pull_thread = threading.Thread(target=pull, args=(mgt,))
    args.pull_thread.start()

@timing
def wait_pull_complete(args, mgt):
    args.pull_thread.join()
    print()
    print('wait_pull_complete:99')
    
def start_acq(args, acq):
    acq.s0.CONTINUOUS = 'start'

def stop_acq(args, acq):
    acq.s0.CONTINUOUS = 'stop'


def run_pair(args, acq, mgt):
    configure_acq(args, acq)
    configure_mgt(args, mgt)

    if args.clear_mem:
        clear_mem(args, mgt)

    start_pull(args, mgt)
    start_acq(args, acq)

    wait_pull_complete(args, mgt)
    stop_acq(args, acq)

    read_data(args, mgt)
    


def run_main(args):
    print(f'uut_pairs: {args.uut_pairs}')
    acqname, mgtname = args.uut_pairs[0].split(',')
    acq = acq400_hapi.factory(acqname)
    mgt = acq400_hapi.Mgt508(mgtname)

    run_pair(args, acq, mgt)

def get_parser():
    parser = argparse.ArgumentParser(description='Controls acq2206+mgt508 deep memory system')
    parser.add_argument('--simulate', type=int, default=0, help='use simulated data and validate')
    parser.add_argument('--clear_mem', type=int, default=0, help='zero memory before run')
    parser.add_argument('--GB', type=int, default=4, help='capture length in gigabytes')
    parser.add_argument('uut_pairs', nargs='+', help="acq2206,mgt508 [a,m] ..")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

