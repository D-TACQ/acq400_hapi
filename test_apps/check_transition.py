#!/usr/bin/python3


"""
[ [UUT1 trigger points],  [UUT2 trigger points] ]
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import argparse


def get_args():
    parser = argparse.ArgumentParser(description='Transition test')

    parser.add_argument('--dir', default='/home/peter/FLARE/', type=str, help="Location of data.")

    parser.add_argument('--cutoff', default=5000, type=int, help="Trigger cutoff point.")

    parser.add_argument('--tol', default=400, type=int,
    help='If cutoff fails then difference between samples is checked, where tol is max difference allowed. ')

    parser.add_argument('--verbose', default=0, type=int, help='Print more status messages.')

    parser.add_argument('uuts', nargs='+', help="Names of uuts to test.")

    args = parser.parse_args()
    return args


def main(args):
    dir_list = next(os.walk(args.dir))[1]
    error_count = 0

    for directory in dir_list:
        uut1_data = np.fromfile(args.dir + directory + "/" + args.uuts[0] + "_CH01", dtype=np.int16)
        uut2_data = np.fromfile(args.dir + directory + "/" + args.uuts[1] + "_CH01", dtype=np.int16)

        # Check where values are less than the specified cutoff.
        # This gives an array of True/False values.
        uut1_transition = uut1_data < args.cutoff
        uut2_transition = uut2_data < args.cutoff

        # Check where the values change from False to True.
        transition_point1 = np.where(np.roll(uut1_transition,1) != uut1_transition)[0]
        transition_point2 = np.where(np.roll(uut2_transition,1) != uut2_transition)[0]

        if args.verbose == 1:
            print("Dir: {}, 132 transition: {}, 133 transition: {}".format(directory, transition_point1, transition_point2))

        # Check if the transition arrays are equal or not.
        if not np.array_equal(uut1_transition, uut2_transition):

            if args.verbose == 1:
                print('Quick test failed. Trying tolerance test.')

            # If the transitions are in different places then check the values
            # of the samples are within the user specified tolerance.
            if np.allclose(uut1_data[49998:50003], uut2_data[49998:50003], atol=args.tol, rtol=0):
                if args.verbose == 1:
                    print('Tolerance test passed.')
                continue

            else:
                print("ERROR FOUND IN DIR: {}".format(directory))
                print("{} transition: {}".format(args.uuts[0], uut1_data[49998:50003]))
                print("{} transition: {}".format(args.uuts[1], uut2_data[49998:50003]))

                error_count += 1

    print("Count of non-matching transitions: {}".format(error_count))
    return None

if __name__ == '__main__':
    args = get_args()
    main(args)
