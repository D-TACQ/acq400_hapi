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

    initial_samples = int(uuts[0].s1.sample_count)

    for index, uut in enumerate(uuts):
        uut.s0.streamtonowhered = 'stop'
        states.append(uut.s0.CONTINUOUS_STATE)
        uut.s1.SIG_sample_count_RESET = '1'
        uut.s1.SIG_sample_count_RESET = '0'


    print("Arming systems now - please wait. Do not trigger yet.")

    for uut in reversed(uuts):
        uut.s0.streamtonowhered = 'start'

    wait_trigger = True
    while not all(elem == 'CONTINUOUS:STATE ARM' for elem in states):
        states = update_states(uuts, states)
        if all(elem == 'CONTINUOUS:STATE RUN' for elem in states):
            wait_trigger = False
            break

    if wait_trigger:
        print("All UUTs are armed and ready for trigger.")
    else:
        print("Didn't see wait for trigger, maybe not start at zero")

    # Included as a comment below is an example of how this
    # script was tested. If the user wishes to automate
    # a test that involves this script then a signal generator
    # may be triggered like so:
    # os.system("echo 'TRIG' | nc 10.12.196.174 5025")

    while not all(elem == 'CONTINUOUS:STATE RUN' for elem in states):
        states = update_states(uuts, states)
        continue

    streamed_samples = 0
    while streamed_samples <= args.samples:
        print("Streamed {} of {} samples".format(streamed_samples, args.samples))
        streamed_samples = acq400_hapi.Acq400.intpv(uuts[0].s1.SIG_sample_count_COUNT)
        time.sleep(1)

    print("\nStream finished.")
    for uut in uuts:
        uut.s0.streamtonowhered = 'stop'


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream to nowhere')

    parser.add_argument('--samples', default=100000, type=int,
    help='The number of samples to stream. Not exact.')

    parser.add_argument('uuts', nargs='+', help="uuts")

    args = parser.parse_args()
    main(args)


if __name__ == '__main__':
    run_main()
