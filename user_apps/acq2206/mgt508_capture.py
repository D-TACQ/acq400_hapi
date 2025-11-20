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
import math
import os
import sys

GB1 = 0x40000000

PULL_BUFFERS_PER_GB = 0x400

def configure_acq(args, acq):
    while acq400_hapi.pv(acq.s0.CONTINUOUS_STATE) != 'IDLE':
            acq.s0.CONTINUOUS = 0
            print(f'WARNING: requesting {acq.uut} to stop')
            time.sleep(1)

    acq.s1.simulate = args.simulate

    sites = None
    spad  = None
    agg = acq.s0.aggregator
    for kv in agg.split(' '):
        key, value = kv.split('=')
        if key == 'sites':
            sites = value
        if key == 'spad':
            spad = value.split(',')[0]

    if sites is None or spad is None:
        print(f'unable to parse aggregator {agg}')
        os.exit(1)
    acq.cA.aggregator = f'sites={sites} spad={spad} on'
    args.ssb = int(acq.s0.ssb)

    if args.samples is not None:
        msg_qual = ""
        if args.decimate > 1:
            args.samples *= args.decimate
            msg_qual = " before decimation"

        capture_bytes = args.samples * args.ssb
        args.GB = math.ceil(capture_bytes/GB1)
        print(f'samples:{args.samples} {msg_qual}, sample-size-bytes:{args.ssb}, bytes:{bytes} setting GB:{args.GB}')


def pull(mgt):
    print(f"Start pull {mgt.uut}")
    mgt.pull()

def configure_mgt(args, mgt):
    mgt.set_capture_length(args.GB * PULL_BUFFERS_PER_GB)
    mgt.s0.ssb = args.ssb

@timing
def clear_mem(args, mgt):
    result = subprocess.run(['./scripts/mgt508_clear_mem', mgt.uut])
    print(f'Return code : {result.returncode}')

@timing
def read_data(args, acq, mgt):
    target_script = os.path.join("user_apps", "acq400", "acq400_stream2.py")
    if args.simulate:
        cols = int(acq.s0.ssb)//4
        read_amount = args.GB
        result = subprocess.run(['./scripts/mgt508_validate_mem', mgt.uut, str(read_amount), str(cols) ])
    elif args.decimate:
        read_amount = args.GB / args.decimate
        cmd = [
        sys.executable,
        target_script,
        "--delete=y",
        "--filesize=128M",
        f"--totaldata={read_amount}G",
        f"--port={mgt.ports.DECIMATE_READ}",
        "--verbose=1",
        mgt.uut
        ]
        result = subprocess.run(cmd, check=True)
    else:
        read_amount = args.GB
        cmd = [
        sys.executable,       # Uses the currently running python.exe / python3
        target_script,
        "--delete=y",
        "--filesize=128M",
        f"--totaldata={read_amount}G", # Replicates the ${2}G from bash
        f"--port={mgt.ports.READ}",
        "--verbose=1",
        mgt.uut
        ]
        result = subprocess.run(cmd, check=True)
    print(f'Return code : {result.returncode}')

def start_pull(args, mgt):
    args.pull_thread = threading.Thread(target=pull, args=(mgt,))
    args.pull_thread.start()

@timing
def wait_pull_complete(args, mgt):
    args.pull_thread.join()
    print()
    print('Pull Complete')
    if mgt.capture_time:
        print(f'Capture {mgt.capture_blocks} time {mgt.capture_time:.2} sec {mgt.capture_blocks*32/mgt.capture_time:.0f} MB/s')
    
def start_acq(args, acq):
    acq.s0.CONTINUOUS = 'start'

def stop_acq(args, acq):
    acq.s0.CONTINUOUS = 'stop'


def run_pair(args, acq, mgt):
    configure_acq(args, acq)
    configure_mgt(args, mgt)

    if args.clear_mem:
        clear_mem(args, mgt)

    if args.pull:
        start_pull(args, mgt)

    start_acq(args, acq)

    if args.pull:
        wait_pull_complete(args, mgt)
    stop_acq(args, acq)

    if args.read:
        read_data(args, acq, mgt)


def run_main(parser):
    args = parser.parse_args()
    print(f'uut_pairs: {args.uut_pairs}')
    acqname, mgtname = args.uut_pairs[0].split(',')
    acq = acq400_hapi.factory(acqname)
    mgt = acq400_hapi.Mgt508(mgtname)
#    if args.decimate not in (0, 2):
#        parser.error("argument '--decimate' only supports values of 0 or 2")
    if args.decimate and args.simulate:
        parser.error("arguments '--simulate' and '--decimate' cannot be used together")
    run_pair(args, acq, mgt)

def get_parser():
    parser = argparse.ArgumentParser(description='Controls acq2206+mgt508 deep memory system')
    parser.add_argument('--simulate', type=int, default=0, help='use simulated data and validate')
    parser.add_argument('--read', type=int, default=1, help='Enable or disable read from MGT to host')
    parser.add_argument('--pull', type=int, default=1, help='Enable or disable pull from ACQ to MGT')
    parser.add_argument('--clear_mem', type=int, default=0, help='zero memory before run')
    parser.add_argument('--samples', type=int, default=None, help='capture length in samples')
    parser.add_argument('--GB', type=int, default=4, help='capture length in gigabytes')
    parser.add_argument('--decimate', type=int, default=0, choices=(0,2), help='Enable or disable 2x decimation during read from MGT to host')
    parser.add_argument('uut_pairs', nargs='+', help="acq2206,mgt508 [a,m] ..")
    return parser

if __name__ == '__main__':
    run_main(get_parser())

