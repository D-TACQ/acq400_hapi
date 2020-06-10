#!/usr/bin/env python


import numpy as np
import argparse
import json


def get_args():
    parser = argparse.ArgumentParser(description='Use wavedrom JSON file for dpg')
    parser.add_argument('--file',  default='./wd.json', help="Which JSON file to use to load dpg.")
    parser.add_argument('--breaks',  default='100', help="How many clock ticks a line break is.")
    parser.add_argument('--print_stl',  default=1, help="Print resultant STL or not.")
    parser.add_argument('--file_name',  default='wd.stl', help="Name of file to save stl to.")
    args = parser.parse_args()
    args.breaks = [ int(item) for item in args.breaks.split(',') ]
    return args


def load_json(json_file):
    with open(json_file) as _json_file:
        dpg_data = json.load(_json_file)
    return dpg_data


def wd2np(wave, breaks):
    # Takes wavedrom syntax and creates a numpy array of 1s and 0s.
    binary_wave = []
    wave = list(wave)
    for num, character in enumerate(wave):
        # print(character)

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
                binary_wave = binary_wave + int(breaks[num]) * [int(wave[num-1])]
            except:
                binary_wave = binary_wave + int(breaks[0]) * [int(wave[num-1])]

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
        change_locations = np.where(np.abs(np.diff(binary_wave)) == 1) + np.array([1])
        change_values = binary_wave[change_locations]
        stl = np.array([change_locations, change_values, binary_wave])
        # channels.append(wd2np(json, breaks))
        channels.append(stl)
    return channels


def chans2stl(channels):
    # indexes = np.concatenate()
    left_col = np.array([])
    for chan in channels:
        left_col = np.concatenate((left_col, chan[0][0]))
    left_col = np.unique(left_col) # removes duplicates and sorts.

    right_col = np.zeros(left_col.shape[-1])
    left_col = left_col.astype(np.uint32)
    for num, chan in enumerate(channels):
        right_col = right_col + (chan[2][left_col] * 2**num)

    left_col = np.concatenate((np.array([0]), left_col))
    right_col = np.concatenate((np.array([0]), right_col))

    stl = np.array([left_col, right_col])
    return stl


def save_stl(stl, file_name):
    with open(file_name, 'w+') as file:
        for num in range(0,len(stl[0])):
            file.write("{} {}\n".format(int(stl[0][num]), hex(int(stl[1][num]))))
    return None


def main():
    args = get_args()
    data = load_json(args.file)
    channels = strip_json(data, args.breaks)
    stl = chans2stl(channels)
    save_stl(stl, args.file_name)
    if args.print_stl:
        for num in range(0,len(stl[0])):
            print(int(stl[0][num]), hex(int(stl[1][num])))
    return None


if __name__ == '__main__':
    main()
