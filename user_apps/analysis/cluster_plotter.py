#!/usr/bin/env python3

import argparse
import glob
import os
import re
import numpy as np
import matplotlib.pyplot as plt

import acq400_hapi
from acq400_hapi import PR

"""
Usage:

./user_apps/analysis/cluster_plotter.py --src=/mnt/afhba.?/acq2206_0??/000001/???? --grouping=2 --chans=1 acq2206_010 acq2206_009 acq2206_008 acq2206_007 acq2206_006 acq2206_005
"""

type_map = {
    32 : {
        'type' : np.int32,
        'wsize' : 4,
    },
    16 : {
        'type' : np.int16,
        'wsize' : 2,
    },
    8 : {
        'type' : np.int8,
        'wsize' : 1,
    },
}

class globals:
    uuts = {}


def run_main(args):
    file_dict = get_files(**vars(args))
    groups = grouper(list(file_dict.keys()), args.grouping)
    file_dict = demux_data(file_dict, args)
    if args.multi:
        plot_data_multi(file_dict, groups, args.combine, args)
    else:
        plot_data(file_dict, groups, args.combine, args)


def get_files(src, uuts, nchan, data_type, **kwargs):
    print('Finding Files')
    file_dict = {}
    for glob_str in src:
        files = glob.glob(glob_str)
        files.sort()

        for filepath in files:
            dirname = os.path.dirname(filepath)
            filename = os.path.basename(filepath)
            if dirname not in file_dict:
                filesize = os.path.getsize(filepath)
                uut = conn_uut(dirname, uuts)
                if not nchan:
                    nchan = int(uut.s0.NCHAN)
                if not data_type:
                    if uut.s0.data32 == 0:
                        data_type = 32
                    else:
                        data_type = 16
                wsize = type_map[data_type]['wsize']
                file_dict[dirname] = {}
                file_dict[dirname]['uut'] = uut
                file_dict[dirname]['chan_len'] = int(filesize / nchan / wsize)
                file_dict[dirname]['total_files'] = 0
                file_dict[dirname]['channels'] = {}
                file_dict[dirname]['files'] = []
                file_dict[dirname]['filesize'] = filesize
                file_dict[dirname]['channels'] = {}
                file_dict[dirname]['data_type'] = type_map[data_type]['type']
                file_dict[dirname]['wsize'] = wsize
                file_dict[dirname]['nchan'] = nchan

            file_dict[dirname]['total_files'] += 1
            file_dict[dirname]['files'].append(filename)

    return file_dict

def conn_uut(path, uuts):
    uutname = identify_uut(path)
    if not uutname:
        uutname = uuts[0]
    if uutname not in globals.uuts:
        PR.Green(f"Connecting to {uutname}")
        globals.uuts[uutname] = acq400_hapi.factory(uutname)
        globals.uuts[uutname].name = uutname
    return globals.uuts[uutname]

def identify_uut(path):
    match =  re.search("(acq[0-9]{4}_[0-9]{3})", path)
    if match:
        return match.group(0)
    return match

def grouper(arr, grouping):
    groups = []
    i = 0
    if not grouping:
        for loc in arr:
            group = {}
            group['loc'] = loc
            group['group'] = [loc]
            groups.append(group)
        return groups
    while arr:
        loc1 =  arr.pop(0)
        loc1_group = loc1.split('/')[-abs(grouping)]
        if not grouping:
            loc1_group = loc1
        current = [loc1]
        i = 0
        while i < len(arr):
            loc2 = arr[i]
            loc2_group = loc2.split('/')[-abs(grouping)]
            if not grouping:
                loc2_group = loc2
            if loc1_group == loc2_group:
                popped = arr.pop(i)
                current.append(popped)
                i -= 1
            i += 1
        group = {}
        group['loc'] = loc1_group
        group['group'] = current
        groups.append(group)
    return groups

def demux_data(file_dict, args):
    print('Demuxing')
    for dirname, item in file_dict.items():
        i0 = 0
        nchan = item['nchan']
        data_type = item['data_type']
        for file in item['files']:

            filepath = os.path.join(dirname, file)
            data = np.fromfile(filepath, dtype=data_type)

            i1 = i0 + item['chan_len']

            for chan in args.chans:

                if chan not in item['channels']:
                    total_files = item['total_files']
                    zero_arr = np.zeros(item['chan_len'] * total_files, dtype=data_type)
                    item['channels'][chan] = zero_arr

                ichan = chan - 1
                item['channels'][chan][i0:i1] = (data[ichan::nchan])
            i0 = i1
        if args.egu:
            args.ylabel = 'volts'
            for chan, data in item['channels'].items():
                item['channels'][chan] = item['uut'].chan2volts(chan, data)

    return file_dict

def plot_data(file_dict, groups, combine, args):
    print('Plotting')
    title = ''
    for i, item in enumerate(groups):

        group = item['group']
        title += f"{group[0]} " 
        group_arrs = {}
        for ii, dirname in enumerate(group):
            for chan, data in file_dict[dirname]['channels'].items():
                if not combine:
                    plt.plot(data, label=item['loc'])
                    continue
                if ii == 0:
                    group_arrs[chan] = []
                group_arrs[chan].append(data)
        if combine:
            for chan, arrs in group_arrs.items():
                plt.plot(np.concatenate(arrs), label=item['loc'])

    plt.title(title)
    plt.ylabel(args.ylabel)
    plt.xlabel(args.xlabel)
    plt.legend(loc='upper right')
    plt.show()

def plot_data_multi(file_dict, groups, combine, args):
    print('Plotting multi')
    fig, axs = plt.subplots(len(groups))
    if len(groups) == 1:
        axs = [axs]
    title = ''
    for i, item in enumerate(groups):
        group = item['group']
        title += f"{group[0]} "
        groupdata = {}
        for ii, dirname in enumerate(group):
            for chan, data in file_dict[dirname]['channels'].items():
                if not combine:
                    axs[i].set_title(item['loc'])
                    axs[i].plot(data)
                if ii == 0:
                    groupdata[chan] = []
                groupdata[chan] = np.append(groupdata[chan], data)
            
        if combine:
            axs[i].set_title(item['loc'])
            for chan, data in groupdata.items():
                axs[i].plot(data)

    plt.title(title)
    plt.ylabel(args.ylabel)
    plt.xlabel(args.xlabel)
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.57, hspace=None)
    plt.show()

def list_of_strings(string):
    return string.split(',')

def list_of_ints(string):
    return list(map(int, string.split(',')))

def get_parser():
    parser = argparse.ArgumentParser(description='Cluster plotter')
    parser.add_argument('--src', default=None, type=list_of_strings, help="glob file source ie /mnt/folder1/*,/mnt/folder2/*")
    parser.add_argument('--grouping', default=0, type=int, help="which path part to group by")
    parser.add_argument('--chans', default=1, type=list_of_ints, help="channels to plot 1,2,3")
    parser.add_argument('--data_type', default=None, type=int, help="Data type to use")
    parser.add_argument('--nchan', default=None, type=int, help="Number of chan")
    parser.add_argument('--egu', default=0, type=int, help="Plot volts")
    parser.add_argument('--combine', default=0, type=int, help="Combine grouped data into single data arr")
    parser.add_argument('--multi', default=0, type=int, help="Plot per group")
    parser.add_argument('--ylabel', default='raw ADC codes', help="Y label to use")
    parser.add_argument('--xlabel', default='Samples', help="X label to use")
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())