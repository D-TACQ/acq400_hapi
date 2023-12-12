#!/usr/bin/env python3

"""
A script that streams using streamtonowhered.
"""

import acq400_hapi
import argparse
import time
import datetime
import subprocess
import os

def update_states(uuts, states):
    for index, uut in enumerate(uuts):
        states[index] = (uut.s0.CONTINUOUS_STATE)
    return states

def main(args):
    uuts = []
    states = []

    for uut in args.uuts:
        uuts.append(acq400_hapi.factory(uut))

    for index, uut in enumerate(uuts):
        uut.s0.streamtonowhered = 'stop'
        states.append(uut.s0.CONTINUOUS_STATE)

    print("Arming systems now - please wait. Do not trigger yet.")

    for uut in reversed(uuts):
        uut.s0.streamtonowhered = 'start'

    while not all(elem == 'CONTINUOUS:STATE ARM' for elem in states):
        states = update_states(uuts, states)

    print("All UUTs are armed and ready for trigger.")

def get_parser():
    parser = argparse.ArgumentParser(description='Start stream to nowhere')
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())