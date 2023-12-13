#!/usr/bin/env python3

"""
Plots data from cluster of uuts

Example usage::

    ./user_apps/analysis/cluster_plotter.py --chans=1 --cycles=1:2 --secs=1 --clk=2M \
acq2206_010 acq2206_009 acq2206_008 acq2206_007 acq2206_006 acq2206_005

    ./user_apps/analysis/cluster_plotter.py --chans=1 --cycles=1:2 --secs=1 --clk=2M --nchan=64 --data_type=16\
acq2206_010 acq2206_009 acq2206_008 acq2206_007 acq2206_006 acq2206_005

    ./user_apps/analysis/cluster_plotter.py --chans=1 --src=acq2106_41?_VI.dat \
acq2106_413 acq2106_414 acq2106_415

"""

import argparse
import glob
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import threading
import acq400_hapi
from collections import namedtuple
from acq400_hapi import PR, pprint

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
data_globs = ['?.??','*.dat']

def run_main(args):
    scaffold = build_scaffold(**vars(args))
    demux(scaffold, **vars(args))
    if args.verbose:
        pprint(scaffold)
    plot(scaffold, **vars(args))

def build_scaffold(src, uuts, data_type, nchan, cycles, clk, secs, offline, egu, spadlen, **kwargs):
    print('building')
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
            dat_files, filesize, first_cycle, per_cycle = get_files(file_src, cycles[0], cycles[-1])
        else:
            dat_files = [file_src]
            filesize = os.path.getsize(file_src)
            scaffold[uutname]['filename'] = file_src
            first_cycle = per_cycle = None

        if offline:
            uut = None
        else:
            uut = attach_api(uutname)

        _data_type = data_type
        if not data_type:
            if not uut:
                exit('--data_type required')
            if int(uut.s0.data32):
                _data_type = 32
            else:
                _data_type = 16

        _nchan = nchan
        if not nchan:
            if not uut:
                exit('--nchan required')
            _nchan = int(uut.get_ai_channels())
            if not spadlen:
                spadlen = int(uut.s0.spad.split(',')[1])
            spad = spadlen * (4 - type_map[_data_type]['wsize'])
            _nchan += spad

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
        
        scaffold[uutname]['dat_files'] = dat_files
        scaffold[uutname]['api'] = uut
        scaffold[uutname]['nchan'] = _nchan
        scaffold[uutname]['clk'] = _clk
        scaffold[uutname]['data_type'] = type_map[_data_type]['type']
        scaffold[uutname]['wsize'] = type_map[_data_type]['wsize']
        scaffold[uutname]['first_cycle'] = first_cycle
        scaffold[uutname]['per_cycle'] = per_cycle
        scaffold[uutname]['cycle_start'] = cycles[0]
        scaffold[uutname]['cycle_end'] = cycles[-1]
        scaffold[uutname]['total_files'] = len(dat_files)
        scaffold[uutname]['file_size'] = filesize
        scaffold[uutname]['chan_len'] = int(filesize / _nchan / type_map[_data_type]['wsize'])
        scaffold[uutname]['data'] = []
        scaffold[uutname]['channels'] = {}
        scaffold[uutname]['num_chans'] = 0

    if not scaffold:
        exit('No valid uuts found')
    
    if len(threads) > 0:
        for thread in threads:
            thread.join()

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
    dat_files = []
    for cycle in range(start, end + 1):
        for data_glob in data_globs:
            file_glob = os.path.join(path, f"{cycle:06d}", data_glob)
            files = glob.glob(file_glob)
            if files:
                break
        files.sort()
        dat_files.extend(files)
    if len(dat_files) == 0:
        exit(f"Error: Unable to find files for glob {path}")
    first_cycle = get_first_cycle(path)
    return dat_files, first_cycle.size, first_cycle.index, first_cycle.files

def get_first_cycle(path):
    first_cycle = namedtuple('first_cycle', ['index', 'files', 'size'])
    for cycle in range(10):
        for data_glob in data_globs:
            files = glob.glob(os.path.join(path, f"{cycle:06d}", data_glob))
            if files:
                return first_cycle(cycle, len(files), os.path.getsize(files[0]))
    exit('Error could not find first cycle')

def demux(scaffold, chans, uuts, **kwargs):
    print('demuxing')
    for uut in uuts:
        item = scaffold[uut]
        nchan = item['nchan']
        data_type = item['data_type']

        for filepath in item['dat_files']:
            item['data'] = np.append(item['data'], np.fromfile(filepath, dtype=data_type))
        for chan in chans:
            if chan > nchan:
                continue
            ichan = chan - 1
            item['num_chans'] += 1
            item['channels'][chan] = item['data'][ichan::nchan]

def plot(scaffold, uuts, secs, egu, verbose, plots, **kwargs):
    print('plotting')
    title = ''
    xlabel = 'Seconds' if secs else 'Samples'
    ylabel = 'Volts' if egu else 'Raw ADC Codes'

    class plt_wrapper:
        def __init__(self, plots, num_chans):
            self.x_arrs = {}
            self.num_chans = num_chans
            if not plots:
                self.num_chans = 1
            self.fig, axes = plt.subplots(self.num_chans, 1, sharex=True)
            self.axes = axes if isinstance(axes, np.ndarray) else [axes]
            self.idx = 0

        def plot(self, data, label=None):
            if egu:
                if not api:
                    exit('no calibration found unable to plot by volts')
                if wsize == 4:
                    data = data / 256
                data = api.chan2volts(chan, data)

            if secs:
                length = len(data)
                if length not in self.x_arrs:
                    self.x_arrs[length] = self.build_x_array(length)
                self.axes[self.idx].plot(self.x_arrs[length], data, label=label)
            else:
                self.axes[self.idx].plot(data, label=label)

            self.axes[self.idx].legend(loc='upper right')
            plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)
            plt.gca().get_yaxis().get_major_formatter().set_useOffset(False)
            if self.num_chans > 1:
                self.idx += 1

        def build_x_array(self, length):
            offset = 0
            if 'filename' not in item and cycle_start > first_cycle:
                offset = chan_len * per_cycle * (cycle_start - first_cycle)
            x_arr = np.arange(offset, length + offset)
            x_arr = x_arr / clk
            return x_arr
        
    num_chans = sum([scaffold[uut]['num_chans'] for uut in uuts])
    wrapper = plt_wrapper(plots, num_chans)

    for uut in uuts:
        item = scaffold[uut]
        cycle_start = item['cycle_start']
        cycle_end = item['cycle_end']
        wsize = item['wsize']
        chan_len = item['chan_len']
        api = item['api']
        clk = item['clk']
        first_cycle = item['first_cycle']
        per_cycle = item['per_cycle']

        if 'filename' in item:
            title += f"{item['filename']} "
        else:
            title = f"{cycle_start:06d} - {cycle_end:06d}"

        for chan, data in scaffold[uut]['channels'].items():
            label = f"{uut} CH{chan}"

            if verbose:
                print(f"{uut} Plotting Chan {chan} length {len(data)}")

            wrapper.plot(data, label)

    wrapper.fig.text(0.5, 0.04, xlabel, ha='center')
    wrapper.fig.text(0.04, 0.5, ylabel, va='center', rotation='vertical')
    wrapper.fig.suptitle(title)
    plt.show()
    print('done')
        
def list_of_channels(chans):
    channels = []
    for chan in chans.split(','):
        if '-' in chan:
            chan = list(map(int, chan.split('-')))
            channels.extend(list(range(chan[0], chan[1] + 1)))
            continue
        channels.append(int(chan))
    return channels

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
    parser = argparse.ArgumentParser(description='Plot data from a cluster of UUTs')
    parser.add_argument('--src', default='/mnt/afhba.*/acq2?06_???', help="src dir")
    parser.add_argument('--chans', default='1', type=list_of_channels, help="channels to plot 1,2,3-5")
    parser.add_argument('--egu', default=0, type=int, help="Plot volts")
    parser.add_argument('--secs',  default=0, type=int, help="Plot secs")
    parser.add_argument('--cycles', default='1', help="single cycle 1 or start end 3:7 to plot")
    parser.add_argument('--nchan', default=None, type=int, help="Number of chan")
    parser.add_argument('--data_type', default=None, type=int, help=f"Data type to use {type_map}")
    parser.add_argument('--clk', default=None, type=prefix_number, help="clk speed")
    parser.add_argument('--offline', default=0, type=int, help="Don't try to connect to uuts")
    parser.add_argument('--verbose', default=0, type=int, help="Increase verbosity")
    parser.add_argument('--plots', default=0, type=int, help="Multi plot")
    parser.add_argument('--spadlen', default=None, type=int, help="Length of spad")
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

