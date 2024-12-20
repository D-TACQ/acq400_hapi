#!/usr/bin/env python3

"""
ALLISON DEMO


Usage:
    ./user_apps/pyepics/allison_demo.py acq2106_176 --translen=20480 --mask=1-6,17-20

"""

import argparse
import numpy as np
from matplotlib import pyplot as plt

from pprint import pprint

from acq400_hapi.acq400e import acq400e, DotDict, States

# Classes
class MaskHelper(DotDict):
    """helper for channel mask"""
    def __init__(self, mask):
        if isinstance(mask, list):
            self.list = sorted(mask)
            self.int = self.to_int()
            self.hex = hex(self.int)

        if isinstance(mask, str):
            self.hex = mask
            self.int = int(mask, 16)
            self.list = self.to_list()

        if isinstance(mask, int):
            self.int = mask
            self.hex = hex(mask)
            self.list = self.to_list()

    def to_list(self):
        return [i + 1 for i in range(self.int.bit_length()) if self.int & (1 << i)]

    def to_int(self):
        return sum(1 << (chan - 1) for chan in self.list)


# Functions

def monitor_cursor(uut, wavelength):
    cursor_pv = "{uut}:0:AO:STEP:CURSOR"

    def cursor_callback(value, **kwargs):
        if value >= wavelength and uut.cstate != States.IDLE.value:
            print('Requesting stop')
            uut.stop_flag = True

    uut.monitor(cursor_pv, cursor_callback)

def get_data_format(nchan, datalen, schan=0, mask=[]):
    """generates dtype for expected data"""

    dtype_map = {
        2: np.int16,
        4: np.int32,
    }

    chans = mask if len(mask) > 1 else list(range(1, nchan + 1))

    format = DotDict({
        'data_t': 0,  # total data channels
        'data_w': datalen, # data channel width

        'spad_t': schan, # total spad channels
        'spad_w': 4,  # spad channel width

        'samp_w': 0, # sample width
        'data_i': [], # indexes of data channels
        'spad_i': [], # indexes of spad channels
        'dtype' : []  # custom dtype for numpy
    })

    format.data_t = nchan - (schan * format.spad_w // format.data_w)
    format.data_i = [chan for chan in chans if chan <= format.data_t]
    format.spad_i = [chan for chan in chans if chan > format.data_t]

    if format.data_w == 2: 
        format.spad_i = format.spad_i[::2]

    for chan in format.data_i:
        id = f"chan_{chan}"
        format.dtype.append((id, dtype_map[format.data_w]))

    cursor = 0
    for chan in format.spad_i:
        id = f"spad_{cursor}"
        format.dtype.append((id, dtype_map[format.spad_w]))
        cursor += 1

    format.dtype = np.dtype(format.dtype)

    format.samp_w = (len(format.data_i) * format.data_w) + (len(format.spad_i) * format.spad_w)

    return format

def make_ramp(uut, site, ampitude, wavelength):
    ramp_up = np.linspace(-ampitude, ampitude, wavelength)
    ramp_dn = np.linspace(ampitude, -ampitude, wavelength)
    cup = ampitude * np.cos(np.linspace(0, np.pi, wavelength))
    sup = ampitude * np.sin(np.linspace(0, np.pi, wavelength))

    uut[site].AO_STEP_1 = ramp_up
    uut[site].AO_STEP_2 = ramp_dn
    uut[site].AO_STEP_3 = cup
    uut[site].AO_STEP_4 = sup

    uut[site].AO_STEP_1_EN = 1
    uut[site].AO_STEP_2_EN = 1
    uut[site].AO_STEP_3_EN = 1
    uut[site].AO_STEP_4_EN = 1

def start_ramp(uut):
    uut.s0.AO_STEP_CURSOR = 0

def read_from_disk(filename, data_format):

    dataset = DotDict()
    dataset.data = np.fromfile(filename, dtype=data_format.dtype)

    dataset.es_indices = find_event_signatures(dataset, data_format.samp_w)
    dataset.es_mask = np.full(len(dataset.data), True)

    if len(dataset.es_indices) > 0: 
        dataset.es_mask[dataset.es_indices] = False
    else:
        print('Warning: no event signatures found')

    dataset.chan = {}
    for chan in data_format.data_i:
        id = f"chan_{chan}"
        dataset.chan[chan] = dataset.data[id][dataset.es_mask]

    dataset.spad = {}
    for idx, _ in enumerate(data_format.spad_i):
        id = f"spad_{idx}"
        dataset.spad[idx] = dataset.data[id]

    return dataset

def find_event_signatures(dataset, ssb):
    signatures = [
        0xaa55f151,
        0xaa55f152,
        0xaa55f154,
    ]
    if ssb % 4 != 0:
        print('Warning unable to find es as sample size is not divisble by 4')
        return []

    #TODO find how to trim channel when using structured ndarry
    # data[:-trim] ? if not divisble by unint32
    #trim = ssb % 4
    #data8 = dataset.data.view(np.uint8)

    chans32 = ssb // 4
    data32 = dataset.data.view(np.uint32).reshape(-1, chans32).T
    for dat in data32:
        for es in signatures:
            indices = np.where(dat == es)[0]
            if len(indices) > 0:
                return indices
    return []

# Stars here

def run_main(args):
    print(args)
    uut = acq400e(args.uut)
    mask = MaskHelper(args.mask)

    args.maxtime = None if args.maxbytes else args.maxtime
    args.pchan = None if args.pchan =='all' else args.pchan
    args.pspad = None if args.pspad =='all' else args.pspad
    
    uut.s0.STREAM__SUBSET__MASK = mask.hex
    if args.translen: uut.s1.RTM__TRANSLEN = args.translen

    monitor_cursor(uut, args.wavelength)

    data_format = get_data_format(int(uut.s0.NCHAN), int(uut.s1.data_len), int(uut.s0.SPAD_LEN_r), mask.list)

    make_ramp(uut, args.ao_site, args.ampitude, args.wavelength)
    start_ramp(uut)

    if args.stream:
        uut.stream_to_disk(data_format.samp_w, maxtime=args.maxtime, maxbytes=args.maxbytes)

    dataset = read_from_disk(uut.datafile, data_format)

    if len(dataset.es_indices) > 0:
        unique_es_diffs = np.unique(np.diff(dataset.es_indices))
        print(f"Event signature intervals {unique_es_diffs}")


    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))

    for chan, data in dataset.chan.items():
        if args.pchan != None and chan not in args.pchan: continue
        label = f"Chan {chan}"
        print(f"Plotting {label}")
        ax1.plot(data, label=label)
    ax1.legend(loc="upper left")

    for spad, data in dataset.spad.items():
        if args.pspad != None and spad not in args.pspad: continue
        label = f"Spad {spad}"
        print(f"Plotting {label}")
        ax2.plot(data, label=label)
    ax2.legend(loc="upper left")

    plt.tight_layout()
    plt.show()

# Argparser

def list_of_channels(arg):
    if arg.lower() == 'all': return arg
    channels = []
    for chan in arg.split(','):
        if '-' in chan:
            chan = list(map(int, chan.split('-')))
            channels.extend(list(range(chan[0], chan[1] + 1)))
            continue
        channels.append(int(chan))
    return channels

def valid_translen(arg):
    arg = int(arg)
    if arg % 1024 == 0: return arg
    raise argparse.ArgumentTypeError(f"Invalid value: {arg}. Must be divisible by 1024.")

def get_parser():
    parser = argparse.ArgumentParser(description="Plotter for FNAL")

    parser.add_argument('--pchan', default='all', type=list_of_channels, help="Channels to plot")
    parser.add_argument('--pspad', default=[1], type=list_of_channels, help="Spads to plot (0 indexed)")

    parser.add_argument('--stream', default=1, type=int, help="to stream or not to stream")
    parser.add_argument('--maxtime', default=None, type=int, help="Stream max time")
    parser.add_argument('--maxbytes', default=None, type=int, help="Stream max bytes")

    parser.add_argument('--stack', default='5', type=list_of_channels, help="channels to stack plot")
    parser.add_argument('--slow', default='1-4', type=list_of_channels, help="channels to slow plot")
    parser.add_argument('--all', default=1, type=int, help="plot all")

    parser.add_argument('--wavelength', default=400, type=int, help="Ramp wavelength")
    parser.add_argument('--ampitude', default=5, type=int, help="Ramp ampitude")
    parser.add_argument('--ao_site', default=5, type=int, help="Site with the ao")
    parser.add_argument('--translen', default=None, type=valid_translen, help="Burst length: any number 1024 - 22000")
    parser.add_argument('--mask', default="1-6,17-20", type=list_of_channels, help="channels in the mask")

    parser.add_argument('uut', help="uut name")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())