#!/usr/bin/python3


"""
[ [UUT1 trigger points],  [UUT2 trigger points] ]
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import argparse


def check_transition_data(transition_data, transition_points, uut_data, directory):

    error_count = 0
    for num, row in enumerate(transition_data):
        if not np.array_equal(row, transition_data[0,0:]):
            
            if args.verbose == 1:
                print('Quick test failed. Trying tolerance test.')

            # If the transitions are in different places then check the values
            # of the samples are within the user specified tolerance.
            tp = int(transition_points[num])
            # print(tp)
            if np.allclose(uut_data[num,0:][tp-2:tp+2], uut_data[0,0:][tp-2:tp+2], atol=args.tol, rtol=0):
                if args.verbose == 1:
                    print('Tolerance test passed.')
                continue

            else:
                
                print("ERROR FOUND IN DIR: {}".format(directory))
                print("{} transition: {}".format(args.uuts[0], uut_data[0,0:][tp-2:tp+2]))
                print("{} transition: {}".format(args.uuts[1], uut_data[num,0:][tp-2:tp+2]))
                error_count += 1
    return error_count


def detect_transition(transition_data, index):
    """
    A function used to find the transition point in a binary array.
    """

    try:
        transition_point = np.where(np.roll(transition_data, 1) != transition_data)[0][1]
    except Exception:
        transition_point = np.where(np.roll(transition_data, 1) != transition_data)[0][0]

    return transition_point


def get_args():
    parser = argparse.ArgumentParser(description='Transition test')

    parser.add_argument('--dir', default='default', type=str, help="Location of data.")

    parser.add_argument('--cutoff', default=5000, type=int, help="Trigger cutoff point.")

    parser.add_argument('--tol', default=400, type=int,
    help='If cutoff fails then difference between samples is checked, where tol is max difference allowed. ')

    parser.add_argument('--verbose', default=0, type=int, help='Print more status messages.')

    parser.add_argument('uuts', nargs='+', help="Names of uuts to test.")

    args = parser.parse_args()

    if args.dir == 'default':
        args.dir = os.getenv('HOME')

    return args


def main(args):
    dir_list = next(os.walk(args.dir))[1]
    error_count = 0

    uuts = args.uuts

    shot_length = np.fromfile(args.dir + dir_list[0] + "/" + args.uuts[0] + "_CH01", dtype=np.int16).shape[-1]
    
    uut_data = np.zeros((len(args.uuts), shot_length))
    transition_data = uut_data.copy()
    transition_points = np.zeros(len(args.uuts))

    for directory in dir_list:
        for num, uut in enumerate(args.uuts):
            uut_data[num,0:] = np.fromfile(args.dir + directory + "/" + uut + "_CH01", dtype=np.int16)
            transition_data[num,0:] = uut_data[num,0:] < args.cutoff
            
            if transition_data[num,0:].all():
                print("There was no transition in this data. Skipping shot {} now.".format(directory))
                break

            transition_points[num] = detect_transition(transition_data[num,0:], num)

        if args.verbose == 1:
            for num, uut in enumerate(uuts):
                print("Dir: {}, {} transition: {}".format(directory, uut, transition_points[num]))

        # Check if the transition arrays are equal or not.
        error_count += check_transition_data(transition_data, transition_points, uut_data, directory)


    print("Count of non-matching transitions: {}".format(error_count))
    return None

if __name__ == '__main__':
    args = get_args()
    main(args)
