#!/usr/bin/env python3


import acq400_hapi
import numpy as np
import matplotlib.pyplot as plt
import argparse
import threading
import os
import time
import sys
from datetime import datetime
import re


file = 0


def get_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--at', type=int, default=0,
                        help="Analysis type. "
                        "Default=0: print 4 samples before and after trg, "
                        "1: Check clock times, "
                        "2: Check transition events against embedded events.")

    parser.add_argument('--nchan', type=int, default=36, help='How many total '
                        'channels the system has (in longs). Default=36')

    parser.add_argument('--spad', type=int, default=4, help='How many longwords'
                        ' the system has. Default=4.')

    parser.add_argument('--lt', type=int, default=1, help='File Loading Type '
                        '1: Load files in order or '
                        '2: Load second to last file (for live analysis)')

    parser.add_argument('dirs', nargs='+', help="uuts")
    args = parser.parse_args()
    return args


def get_file(args, directory):
    global file

    file_counter = int(file // 1)
    if not os.path.isdir(directory):
        print("Dir passed to thread: {} does not exist.".format(directory))
        sys.exit(1)

    while True:

        latest_dir = [x[0] for x in os.walk(directory)][-1]
        files = ["{}/{}".format(latest_dir, file)
                 for file in os.listdir(latest_dir)]
        files.sort(key=os.path.getmtime, reverse=False)
        if len(files) < 2:
            time.sleep(1)
            continue

        if args.lt == 1:
            return_file = "{}/{:04}".format(latest_dir, file_counter)
        if args.lt == 2:
            return_file = files[-2]
        if not os.path.isfile(return_file):
            print("No more valid files found. Exiting now.")
            sys.exit(0)
        print(return_file)
        file += 0.5
        return return_file


def get_event_times(args, data):
    times = []
    for uut_data in data:
        spad = uut_data[:, args.nchan-args.spad:]
        diff = np.abs(np.diff(spad, axis=0))
        event_locations = np.where(diff[:, 2] != 0)[0]+1
        event_times = spad[event_locations][:, -1]
        times.append([event_locations, event_times])

    return times


def get_transition_times(data):
    """
    Returns a list:
    [[UUT1 transition times, UUT1 transition locations]
    ,[UUT2 transition times, UUT2 transition locations]...]
    """
    times = []
    for uut_data in data:
        threshold = 1.3e9
        channel = uut_data[:, 0]
        diffs = np.abs(np.diff(channel))
        transition_locations = np.where(diffs > threshold)[0]+1
        transition_times = uut_data[:, -1]

        times.append([transition_times, transition_locations])
    return times


def extract_data(args, file):
    """
    Returns a list:
    [[UUT1 event times, UUT1 event locations]
    ,[UUT2 event times, UUT2 event locations]...]
    """
    data = np.fromfile(file, dtype=np.int32)
    dim = args.nchan
    max_index = (len(data)//dim)*dim
    data = data[0:max_index]
    data = data.reshape(-1, args.nchan)
    return data


def get_neighbours(index, data, n_neighbours):
    neighbours = []
    for indice in range(index-n_neighbours, index+n_neighbours+1):
        if indice > len(data)-1 or indice < 0:
            neighbours.append(0)
            continue
        else:
            neighbours.append(np.around(data[indice]/(2**31)*5, decimals=3))
    return neighbours


def print_data(args, uut_data, transition_data):
    FF = "{:>8}"*9 + "\n"
    rc = []

    for value in transition_data[0][1]:
        for num, uut in enumerate(uut_data):
            neighbours = get_neighbours(value, uut_data[num][:, 0], 4)
            print("UUT {}: ".format(num), FF.format(
                *[str(val) for val in neighbours]))
        print()
    rc = []

    return None


def print_table(args, data, transition_data, event_data):
    FF = "{:>12}" * 3 + "{:>25}"*2 + "\n" + "{:>12}" * 3 + "{:>25}"*2 + "\n"
    event_data = np.array(event_data)

    min = event_data[0][1].shape[0]
    for uut_data in event_data:
        shape = uut_data[1].shape[0]
        min = shape if shape < min else min

    for num, uut_data in enumerate(event_data):
        event_data[num][0] = event_data[num][0][0:min]
        event_data[num][1] = event_data[num][1][0:min]

    diffs = np.abs(np.diff(event_data, axis=0)[0][1])
    mean = np.around(np.mean(diffs), 3)
    min = np.amin(diffs)
    max = np.amax(diffs)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print(FF.format("Min (us)", "Max (us)", "Mean (us)", "Total events", "Last update",
                    min, max, mean, diffs.shape[-1], now))

    return None


def print_transition_check(args, data, transition_data, event_data):
    FF = "{:>10}" * 3
    data[0] = data[0].reshape((-1, args.nchan))
    change_indices_detected = data[0][transition_data[0][1]][:, args.nchan-args.spad]
    change_indices_real = data[0][event_data[0][0]][:, args.nchan-2]
    diffs = []
    for item in change_indices_real:
        xx = change_indices_detected
        difference = np.abs(item-xx[np.abs(xx - item).argmin()])
        diffs.append(difference)

    mean = np.around(np.mean(diffs), 3)
    min = np.amin(diffs)
    max = np.amax(diffs)
    print(FF.format("Min", "Max", "Mean"))
    print(FF.format(min, max, mean))
    global iter
    if max > 1 and diffs[0] < 60:
        print("Max > 1 detected. Exiting now.")
        print(diffs)
        sys.exit(1)

    return None


def analyse_data(args, data):
    transition_data = get_transition_times(data)
    event_data = get_event_times(args, data)

    if args.at == 1:
        print_data(args, data, transition_data)
    if args.at == 2:
        print_table(args, data, transition_data, event_data)
    if args.at == 3:
        print_transition_check(args, data, transition_data, event_data)
    return None


def main():
    args = get_args()
    data = []
    new_data_file = None
    old_data_file = None
    file_timer = 0

    while True:
        for directory in args.dirs:
            new_data_file = get_file(args, directory)
            while new_data_file == old_data_file:
                file_timer += 1
                if file_timer > 600:
                    print("No new files detected. Exiting now.")
                    sys.exit(1)
                else:
                    time.sleep(1)
                    new_data_file = get_file(directory)
                    continue

            file_timer = 0
            data.append(extract_data(args, new_data_file))
        if len(data) < 2:
            continue
        analyse_data(args, data)
        data = []
        old_data_file = new_data_file


if __name__ == '__main__':
    main()
