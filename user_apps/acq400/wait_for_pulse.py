#!/usr/bin/env python


"""
wait_for_pulse.py is a script that monitors the number of trigger pulses that
the UUT recieves and sends the abort command once n triggers have passed.

The script is intended to be run before starting a stream. For example, if the
user wanted to start the stream on one trigger and stop the stream on the next
trigger, then the user would set --n=2 as such::

    ./wait_for_pulse.py --n=2 --reset=1 acq2106_085

The reset parameter shown above sets the counter to 0.

wait_for_pulse MUST be running BEFORE the stream starts
wait_for_pulse does NOT start the stream, some other agent must do that.
wait_for_pulse will STOP the stream
"""


import acq400_hapi
import numpy as np
import matplotlib.pyplot as plt
import argparse


def run(args):
    uuts = []
    for uut in args.uuts:
        uuts.append(acq400_hapi.Acq400(uut))

    if args.reset == 1:
        for uut in uuts:
            uut.s0.SIG_TRG_EXT_RESET = 1
            while int(uut.s0.SIG_TRG_EXT_COUNT.split(" ")[1]) != 0:
                uut.s0.SIG_TRG_EXT_RESET = 1
                continue

    first_counters = []
    for uut in uuts:
        first_counters.append(int(uut.s0.SIG_TRG_EXT_COUNT.split(" ")[1]))

    counter = 1
    current_trg = int(uuts[0].s0.SIG_TRG_EXT_COUNT.split(" ")[1])
    end_trg = current_trg + args.n

    print("Setup complete: Please start stream now.")

    while current_trg < end_trg:
        current_trg = int(uuts[0].s0.SIG_TRG_EXT_COUNT.split(" ")[1])
        if args.verbose == 1:
            print("Loop {}. Current = {}, End = {}"
                .format(counter, current_trg, end_trg))
        counter += 1

    for uut in uuts:
        uut.s0.set_abort = 1

    print("Number of triggers met. System has been stopped. Quitting now.")

    for pos, uut in enumerate(uuts):

        if int(uut.s0.SIG_TRG_EXT_COUNT.split(" ")[1]) != first_counters[pos] + args.n:

            print("WARNING: {} final trigger pulse counter does not equal its " \
            "starting counter + {}. Please check for configuration errors."
            .format(uut.s0.HN, args.n))

    return None

def get_parser():
    parser = argparse.ArgumentParser(description='stop after n triggers')

    parser.add_argument('--n', default=2, type=int,
    help="How many trgs to wait through before sending abort cmd. Default: 2")

    parser.add_argument('--reset', default=0, type=int,
    help='Whether or not to reset the trg counter before starting. Default: 0')

    parser.add_argument('--verbose', default=0, type=int,
    help='Whether or not to print status messages during operation. Default: 0')

    parser.add_argument('uuts', nargs='+', help="uut list")
    return parser

if __name__ == '__main__':
    run(get_parser().parse_args())
