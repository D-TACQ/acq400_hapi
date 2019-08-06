#!/usr/bin/env python


"""
n-trg-abort.py is a script that monitors the number of triggers that the UUT
recieves and sends the abort command once n triggers have passed.

The script is intended to be run before starting a stream. For example, if the
user wanted to start the stream on one trigger and stop the stream on the next
trigger, then the user would set --n=2 as such:

./n-trg-abort.py --n=2 --reset=1 acq2106_085

The reset parameter shown above sets the counter to 0
"""


import acq400_hapi
import numpy as np
import matplotlib.pyplot as plt
import argparse


def run(args):

    uut = acq400_hapi.Acq400(args.uut[0])

    if args.reset == 1:
        uut.s0.SIG_TRG_EXT_RESET = 1
        while int(uut.s0.SIG_TRG_EXT_COUNT.split(" ")[1]) != 0:
            continue

    counter = 1
    current_trg = int(uut.s0.SIG_TRG_EXT_COUNT.split(" ")[1])
    end_trg = current_trg + args.n

    print("Setup complete: Please start stream now.")

    while current_trg < end_trg:
        current_trg = int(uut.s0.SIG_TRG_EXT_COUNT.split(" ")[1])
        if args.verbose == 1:
            print("Loop {}. Current = {}, End = {}".format(counter, current_trg, end_trg))
        counter += 1

    uut.s0.set_abort = 1
    print("Number of triggers met. System has been aborted. Quitting now.")
    return None


def main():
    parser = argparse.ArgumentParser(description='stop after n triggers')

    parser.add_argument('--n', default=2, type=int,
    help="How many trgs to wait through before sending abort cmd. Default: 2")

    parser.add_argument('--reset', default=0, type=int,
    help='Whether or not to reset the trg counter before starting. Default: 0')

    parser.add_argument('--verbose', default=0, type=int,
    help='Whether or not to print status messages during operation. Default: 0')

    parser.add_argument('uut', nargs=1, help="uut ")

    run(parser.parse_args())


if __name__ == '__main__':
    main()
