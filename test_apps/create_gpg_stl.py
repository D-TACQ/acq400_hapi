#!/usr/bin/env python


import numpy as np
import argparse
import json


def get_args():
    parser = argparse.ArgumentParser(
        description='Use wavedrom JSON file for dpg')
    parser.add_argument('--wd_input_file',  default='./wd.json',
                        help="Which JSON file to use to load dpg.")
    parser.add_argument('--breaks',  default='100',
                        help="How many clock ticks a line break is.")
    parser.add_argument('--print_stl',  default=1,
                        help="Print resultant STL or not.")
    parser.add_argument('--wd_output_file',  default='wd.stl',
                        help="Name of file to save stl to.")
    parser.add_argument('--stl', default='none', type=str,
                        help='If this option is used then single channel STL files can be used. For more info see README_WAVEDROM.md')

    args = parser.parse_args()

    if args.stl != 'none':
        args.stl = args.stl.split(',')
        args.stl = [string.split('=') for string in args.stl]

    args.breaks = [int(item) for item in args.breaks.split(',')]
    return args


def load_json(json_file):
    with open(json_file) as _json_file:
        dpg_data = json.load(_json_file)
    return dpg_data


def wd2np(wave, breaks):
    # Takes wavedrom syntax and creates a numpy array of 1s and 0s.
    binary_wave = []
    wave = list(wave)
    break_counter = 0
    for num, character in enumerate(wave):

        if character == '1':
            binary_wave.append(1)
        elif character == '0':
            binary_wave.append(0)
        elif character == '.':
            binary_wave.append(int(wave[num-1]))
            wave[num] = int(wave[num-1])
        elif character == '|':
            # Treat pipe as breaks * last state where breaks is either always
            # the same value, or is a list of values.
            try:
                binary_wave = binary_wave + \
                    int(breaks[break_counter]) * [int(wave[num-1])]
                break_counter += 1
            except:
                binary_wave = binary_wave + \
                    int(breaks[-1]) * [int(wave[num-1])]

    return np.array(binary_wave)


def strip_json(json, breaks):
    json['signal']
    channels = []
    for chan in json['signal']:
        wave = chan['wave']
        binary_wave = wd2np(wave, breaks)

        # Take the diff to find the locations where the value changes, then use
        # abs to change -1s to 1s, then use where to only take the locations
        # of somewhere that changes and add one since the dimension of the new
        # array is off by 1 since we took the diff.
        change_locations = np.where(
            np.abs(np.diff(binary_wave)) == 1) + np.array([1])
        stl = np.array([change_locations, binary_wave])
        channels.append(stl)
    return channels


def chans2stl(channels):
    # This function takes a list of N channels, each with 2 sublists where
    # the first sublist is the location of any changes in value in the second
    # list, the second is a full binary array of 1s and 0s for that channel.

    left_col = np.array([])
    for chan in channels:
        # Append all of the locations of a change in value to left_col.
        left_col = np.concatenate((left_col, chan[0][0]))
    left_col = np.unique(left_col)  # removes duplicate entries and sorts.
    right_col = np.zeros(left_col.shape[-1])
    left_col = left_col.astype(np.uint32)

    for num, chan in enumerate(channels):
        # For each change in value add (value ** N) where N = channel index (1,2,3 etc).
        if len(chan[1]) < left_col[-1]:
            # If one ch has more entries than another extend chs that are short.
            difference = int(left_col[-1] - len(chan[1])) + 1
            extension = np.full((1, difference), int(chan[1][-1]))[0]
            chan[1] = np.concatenate((chan[1], extension))

        right_col += (chan[1][left_col] * 2**num)

    if left_col[0] != 0:
        left_col = np.concatenate((np.array([0]), left_col))
        right_col = np.concatenate((np.array([0]), right_col))

    stl = np.array([left_col, right_col])
    return stl


def save_stl(stl, output_file):
    with open(output_file, 'w+') as file:
        for num in range(0, len(stl[0])):
            file.write("{} {}\n".format(
                int(stl[0][num]), hex(int(stl[1][num]))))
    return None


def load_stl(stl_desc):
    # Takes the stl description and creates a channels list from it.
    # The channels list is a list of pairs of arrays, where the first array is
    # the locations of the changes and the second array is the entire range
    # of binary values.
    channels = []
    for index, file in enumerate(stl_desc):
        with open(file[1]) as file:
            stl = file.read()
        stl = [string.split(" ") for string in stl.split("\n")][:-1]
        left = [int(item[0]) for item in stl]
        right = [int(item[1]) for item in stl]
        right_col = np.array([])
        diff = np.diff(left)
        for num, item in enumerate(diff):
            # Assumes first entry is always zero
            right_col = np.concatenate((right_col, [right[num]] * (item)))
        right_col = np.concatenate((right_col, [right[-1]]))
        stl = np.array([[left], np.array(right_col)])
        channels.append(stl)
    return channels


def main():
    args = get_args()

    if args.stl == 'none':
        # If the user has not specified an STL assume using JSON.
        data = load_json(args.wd_input_file)
        channels = strip_json(data, args.breaks)
    else:
        channels = load_stl(args.stl)

    stl = chans2stl(channels)
    save_stl(stl, args.wd_output_file)
    if args.print_stl:
        for num in range(0, len(stl[0])):
            print(int(stl[0][num]), hex(int(stl[1][num])))
    return None


if __name__ == '__main__':
    main()
