#!/usr/bin/env python3

import argparse
import glob
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import threading
import acq400_hapi
from acq400_hapi import PR, pprint

"""
Usage:

./user_apps/analysis/cluster_plotter.py --chans=1 --cycles=1:2 --secs=1 --clk=2M \
    acq2206_010 acq2206_009 acq2206_008 acq2206_007 acq2206_006 acq2206_005

./user_apps/analysis/cluster_plotter.py --chans=1 --cycles=1:2 --secs=1 --clk=2M --nchan=64 --data_type=16\
    acq2206_010 acq2206_009 acq2206_008 acq2206_007 acq2206_006 acq2206_005

./user_apps/analysis/cluster_plotter.py --chans=1 --src=acq2106_41?_VI.dat \
    acq2106_413 acq2106_414 acq2106_415
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

def run_main(args):
    scaffold = build_scaffold(**vars(args))
    if args.verbose:
        pprint(scaffold)
    demux_and_plot(scaffold, **vars(args))

def build_scaffold(src, uuts, data_type, nchan, cycles, clk, secs, offline, egu,**kwargs):
    print('setup')
    scaffold = {}
    threads = []
    globbed_src = sorted(glob.glob(src))
    cycles = list(map(int, cycles.split(':')))
    for file_src in globbed_src:
        uutname = identify_uut(file_src)
        if uutname not in uuts:
            continue

        scaffold[uutname] = {}
        scaffold[uutname]['path'] = file_src
        if os.path.isdir(file_src):
            dat_files, total_files, filesize = get_files(file_src, cycles[0], cycles[-1])
        else:
            dat_files = [file_src]
            total_files = 1
            filesize = os.path.getsize(file_src)
            scaffold[uutname]['filename'] = file_src

        if offline:
            uut = None
        else:
            uut = attach_api(uutname)

        _nchan = nchan
        if not nchan:
            if not uut:
                exit('--nchan required')
            _nchan = int(uut.s0.NCHAN)
            spad = int(uut.s0.spad.split(',')[1])
            _nchan += spad

        _data_type = data_type
        if not data_type:
            if not uut:
                exit('--data_type required')
            if int(uut.s0.data32):
                _data_type = 32
            else:
                _data_type = 16

        _clk = clk
        if not clk and secs:
            if not uut:
                exit('--secs needs --clk')
            _clk = int(acq400_hapi.pv(uut.s0.SIG_CLK_MB_SET))
            if hasattr(uut.s1, 'ACQ480_FPGA_DECIM'):
                decim = int(acq400_hapi.pv(uut.s1.ACQ480_FPGA_DECIM))
                _clk = int(_clk / decim)

        if egu:
            thread = threading.Thread(target=uut.fetch_all_calibration)
            thread.start()
            threads.append(thread)
        
        scaffold[uutname]['api'] = uut
        scaffold[uutname]['nchan'] = _nchan
        scaffold[uutname]['clk'] = _clk
        scaffold[uutname]['data_type'] = type_map[_data_type]['type']
        scaffold[uutname]['wsize'] = type_map[_data_type]['wsize']
        scaffold[uutname]['cycle_start'] = cycles[0]
        scaffold[uutname]['cycle_end'] = cycles[-1]
        scaffold[uutname]['dat_files'] = dat_files
        scaffold[uutname]['total_files'] = total_files
        scaffold[uutname]['file_size'] = filesize
        scaffold[uutname]['chan_len'] = int(filesize / _nchan / type_map[_data_type]['wsize'])
        scaffold[uutname]['data'] = {}

    if not scaffold:
        exit('No valid uuts found')
    
    if len(threads) > 0:
        for thread in threads:
            thread.join()


    print(f"Clk: {_clk}")
    print(f"Nchan: {_nchan}")
    print(f"Data type: {_data_type}")
    return scaffold

def identify_uut(path):
    match =  re.search("(acq[0-9]{4}_[0-9]{3})", path)
    if match:
        return match.group(0)
    return match

def attach_api(uutname):
    try:
        return acq400_hapi.factory(uutname)
    except:
        print(f"unable to connect to {uutname}")
        return None
    
def get_files(path, start, end):
    file_list = []
    total_files = 0
    size = None
    data_globs = ['?.??','*.dat']
    for cycle in range(start, end + 1):
        for data_glob in data_globs:
            file_glob = os.path.join(path, f"{cycle:06d}", data_glob)
            files = glob.glob(file_glob)
            if files:
                break
        files.sort()
        total_files += len(files)
        file_list.extend(files)
    if len(file_list) == 0:
        exit(f"Error: Unable to find files for glob {path}")
    size = os.path.getsize(file_list[0])
    return file_list, total_files, size

def demux_and_plot(scaffold, chans, egu, secs, uuts, per_cycle, **kwargs):
    print('demuxing data')
    title = ''
    x_arr = []
    for uut in uuts:
        item = scaffold[uut]

        i0 = 0
        nchan = item['nchan']
        data_type = item['data_type']
        total_files = item['total_files']
        chan_len = item['chan_len']
        cycle_start = item['cycle_start']
        cycle_end = item['cycle_end']
        wsize = item['wsize']
        if 'filename' in item:
            title += f"{item['filename']} "
        else:
            title = f"{cycle_start:06d} - {cycle_end:06d}"

        for filepath in item['dat_files']:
            i1 = i0 + item['chan_len']
            #add concat here
            data = np.fromfile(filepath, dtype=data_type)
            for chan in chans:
                if chan > nchan:
                    continue
                ichan = chan - 1
                if chan not in item['data']:
                    item['data'][chan] = np.zeros(chan_len * total_files, dtype=data_type)

                try:
                    item['data'][chan][i0:i1] = (data[ichan::nchan])
                except Exception as e:
                    print(e)
                    exit('Bad nchan value')
            i0 = i1

        if egu:
            if not item['api']:
                exit('no calibration unable to plot by volts')
            for chan in item['data']:
                if wsize == 4:
                    item['data'][chan] = item['data'][chan]/256
                item['data'][chan] = item['api'].chan2volts(chan, item['data'][chan])

        print(f"{uut} Plotted")
        if secs:
            if len(x_arr) == 0:
                offset = 0
                if cycle_start > 1:
                    offset = chan_len * per_cycle * (cycle_start - 1)
                length = len(list(item['data'].values())[0])
                x_arr = np.arange(offset, length + offset)
                x_arr = x_arr / item['clk']

        for chan in chans:
            label = f"{uut} CH{chan}"
            if chan not in item['data']:
                continue
            if len(x_arr) == 0:
                plt.plot(item['data'][chan], label=label)
                continue
            plt.plot(x_arr, item['data'][chan], label=label)

    print('Showing plot')
    plt.legend(loc='upper right')
    plt.xlabel('Samples')
    plt.ylabel('raw ADC codes')
    if egu:
        plt.ylabel('Volts')
    if secs:
        plt.xlabel('Seconds')
    plt.title(title)
    plt.show()

def list_of_ints(string):
    return list(map(int, string.split(',')))

def prefix_number(value):
    prefixes = {
        'K': 1000,
        'M': 1000000,
    }
    if value[-1] in prefixes:
        num, mag = value[:-1], value[-1]
        return int(float(num) * prefixes[mag])
    else:
        return int(value)


def get_parser():
    parser = argparse.ArgumentParser(description='Cluster plotter')
    parser.add_argument('--src', default='/mnt/afhba.*/acq2?06_???', help="src dir")
    parser.add_argument('--chans', default=1, type=list_of_ints, help="channels to plot 1,2,3")
    parser.add_argument('--egu', default=0, type=int, help="Plot volts")
    parser.add_argument('--secs',  default=0, type=int, help="Plot secs")
    parser.add_argument('--cycles', default='1', help="single cycle 1 or start end 3:7 to plot")
    parser.add_argument('--nchan', default=None, type=int, help="Number of chan")
    parser.add_argument('--data_type', default=None, type=int, help=f"Data type to use {type_map}")
    parser.add_argument('--clk', default=None, type=prefix_number, help="clk speed")
    parser.add_argument('--offline', default=0, type=int, help="Don't try to connect to uuts")
    parser.add_argument('--verbose', default=0, type=int, help="Increase verbosity")
    parser.add_argument('--per_cycle', default=66, type=int, help="Files per cycle")
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
