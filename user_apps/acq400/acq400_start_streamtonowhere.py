#!/usr/bin/env python3

"""
A script that streams N samples using streamtonowhered.
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
        uuts.append(acq400_hapi.Acq400(uut))

    for index, uut in enumerate(uuts):
        uut.s0.streamtonowhered = 'stop'
        states.append(uut.s0.CONTINUOUS_STATE)

    print("Arming systems now - please wait. Do not trigger yet.")

    for uut in reversed(uuts):
        uut.s0.streamtonowhered = 'start'

    while not all(elem == 'CONTINUOUS:STATE ARM' for elem in states):
        states = update_states(uuts, states)

    print("All UUTs are armed and ready for trigger.")


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream to nowhere')

    parser.add_argument('uuts', nargs='+', help="uuts")

    args = parser.parse_args()
    main(args)


if __name__ == '__main__':
    run_main()