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
                        help="Analysis type. Default=0:"
                        "print 4 samples before and after trg,"
                        "1: Check clock times.")

    parser.add_argument('dirs', nargs='+', help="uuts")
    args = parser.parse_args()
    return args


def get_file(directory):
    global file

    file_counter = int(file // 1)
    if not os.path.isdir(directory):
        print("Dir passed to thread: {} does not exist.".format(directory))
        sys.exit(1)
    while True:

        latest_dir = [x[0] for x in os.walk(directory)][-1]
        files = [ "{}/{}".format(latest_dir, file)
                    for file in os.listdir(latest_dir) ]
        files.sort(key=os.path.getmtime, reverse=False)
        if len(files) < 2:
            time.sleep(1)
            continue
        # return_file = files[-2]
        return_file = "{}/{:04}".format(latest_dir, file_counter)
        print(return_file)
        file += 0.5
        return return_file


def get_event_times(data):
    times = []
    for uut_data in data:
        # print(spad)
        spad = uut_data[:, 32:]
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
        transition_times = uut_data[:, -1]  # last column is the time

        times.append([transition_times, transition_locations])
    return times


def extract_data(file):
    """
    Returns a list:
    [[UUT1 event times, UUT1 event locations]
    ,[UUT2 event times, UUT2 event locations]...]
    """
    data = np.fromfile(file, dtype=np.int32)
    dim = 36
    max_index = (len(data)//dim)*dim
    data = data[0:max_index]
    data = data.reshape(-1, 36)
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


def print_data(uut_data, transition_data):
    print(uut_data[0].shape)
    FF = "{:>8}"*9 + "\n"
    rc = []

    for value in transition_data[0][1]:  # for entry in locations
        for num, uut in enumerate(uut_data):
            neighbours = get_neighbours(value, uut_data[num][:, 0], 4)
            print("UUT {}: ".format(num), FF.format(
                *[str(val) for val in neighbours]))
        print()
    rc = []

    return None


def print_table(data, transition_data, event_data):
    spad = [uut_data[:, 32:] for uut_data in data]
    FF = "{:>12}" * 3 + "{:>25}"*2 + "\n" + "{:>12}" * 3 + "{:>25}"*2 + "\n"
    # FF = "{:>25}"*5 + "\n" + "{:>25}"*5 + "\n"
    # print(np.array(event_data).shape)
    event_data = np.array(event_data)
    diffs = np.abs(np.diff(event_data, axis=0)[0][1])
    mean = np.around(np.mean(diffs), 3)
    min = np.amin(diffs)
    max = np.amax(diffs)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print(FF.format("Min (us)","Max (us)","Mean (us)","Total events","Last update",
                     min, max, mean, diffs.shape[-1],now))

    return None


def print_transition_check(data, transition_data, event_data):
    FF = "{:>10}" * 3
    data[0] = data[0].reshape((-1,36))
    # spad1 @ transitions
    change_indices_detected = data[0][transition_data[0][1]][:, 32]
    # Spad3 when spad3 changes
    change_indices_real = data[0][event_data[0][0]][:, 34]
    diffs = []
    for item in change_indices_real:
        # find the difference between item and the closest transition point
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
    event_data = get_event_times(data)

    if args.at == 1:
        print_data(data, transition_data)
    if args.at == 2:
        print_table(data, transition_data, event_data)
    if args.at == 3:
        print_transition_check(data, transition_data, event_data)
    return None


def main():
    args = get_args()
    data = []
    new_data_file = None
    old_data_file = None
    file_timer = 0

    while True:
        for directory in args.dirs:
            new_data_file = get_file(directory)
            # print(new_data_file)
            while new_data_file == old_data_file:
                # print("New = Old")
                # print(old_data_file)
                file_timer += 1
                if file_timer > 600:
                    print("No new files detected. Exiting now.")
                    sys.exit(1)
                else:
                    time.sleep(1)
                    new_data_file = get_file(directory)
                    # break
                    continue

            file_timer = 0
            data.append(extract_data(new_data_file))
        if len(data) < 2:
            continue
        # print(len(data))
        analyse_data(args, data)
        data = []
        old_data_file = new_data_file


if __name__ == '__main__':
    main()
