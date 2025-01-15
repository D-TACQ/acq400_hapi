#!/usr/bin/env python3

"""
ALLISON DEMO


Usage:
    ./user_apps/pyepics/allison_demo.py acq2106_176 --translen=20480 --mask=1-6,17-20 --slow=1,2,3,4 --stack=5

"""

import argparse
import socket
import time

import numpy as np
from matplotlib import pyplot as plt
import epics
import os

# Classes

class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

ai_site = 1
sc_site = 0

class PVHelper(dict):
    def __init__(self, uut, ao_site, trace=False):
        self.uut = uut
        self.datafile = f"{uut}.dat"
        self.stop_flag = False

        self.cstate = None
        cstate_callback = lambda value, **kwargs: setattr(self, 'cstate', value)
        self.cstate_pv = epics.PV("{uut}:MODE:CONTINUOUS:STATE".format(uut=uut), callback=cstate_callback, auto_monitor=True)

        self.tstate = None
        tstate_callback = lambda value, **kwargs: setattr(self, 'tstate', value)
        self.tstate_pv = epics.PV("{uut}:MODE:TRANS_ACT:STATE".format(uut=uut), callback=tstate_callback, auto_monitor=True)

        pvmap = [
            (sc_site, "STREAM_SUBSET_MASK"),
            (0, "NCHAN"),
            (0, "SPAD:LEN:r"),
            (0, "SSB"),
            (0, "AO:STEP:CURSOR"),
            (0, "SIG:TRG_EXT:FREQ"),
            (1, "data32"),
            (1, "RTM_TRANSLEN"),
            (1, "AI:CAL:ESLO"),
            (1, "AI:CAL:EOFF"),
            (ao_site, 'AO:STEP:1'),
            (ao_site, 'AO:STEP:2'),
            (ao_site, 'AO:STEP:3'),
            (ao_site, 'AO:STEP:4'),
            (ao_site, 'AO:STEP:1:EN'),
            (ao_site, 'AO:STEP:2:EN'),
            (ao_site, 'AO:STEP:3:EN'),
            (ao_site, 'AO:STEP:4:EN'),
        ]

        self.PV.trace = trace

        for (site, pvname) in pvmap:
            self[pvname] = self.PV(f"{uut}:{site}:{pvname}")
            #setattr(self, pvname.replace(':', '_'), epics.PV(f"{uut}:{site}:{pvname}"))

    class PV(epics.PV):
        trace = False

        def get(self, *args, **kwargs):
            if not self.trace:
                return super().get(*args, **kwargs)
            host, site, pv = self.pvname.split(':', maxsplit=2)
            print(f"[{host}, {site}] > {pv}")
            value = super().get(*args, **kwargs)
            print(f"[{host}, {site}] < {value}")
            return value
        
        def put(self, *args, **kwargs):
            if not self.trace:
                return super().put(*args, **kwargs)
            value = kwargs.get("value") if "value" in kwargs else args[0]
            host, site, pv = self.pvname.split(':', maxsplit=2)
            print(f"[{host}, {site}] > {pv} = {value}")
            value = super().put(*args, **kwargs)
            print(f"[{host}, {site}] < {value}")
            return value

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

    # this appears to be sample size in bytes ssb?. Maybe call it ssb..
    format.samp_w = (len(format.data_i) * format.data_w) + (len(format.spad_i) * format.spad_w)

    return format

def setup_ramp(pvs, amplitude, scan_steps, ao_step_en):
    ramp_up = np.linspace(-amplitude, amplitude, scan_steps)
    ramp_dn = np.linspace(amplitude, -amplitude, scan_steps)
    cup = amplitude * np.cos(np.linspace(0, np.pi, scan_steps))
    sup = amplitude * np.sin(np.linspace(0, np.pi, scan_steps))

    pvs['AO:STEP:1'].put(ramp_up, wait=True)
    pvs['AO:STEP:2'].put(ramp_dn, wait=True)
    pvs['AO:STEP:3'].put(cup, wait=True)
    pvs['AO:STEP:4'].put(sup, wait=True)

   
    if ao_step_en:
        print("Enabling ao_step_en")
        pvs['AO:STEP:1:EN'].put(1, wait=True)
        pvs['AO:STEP:2:EN'].put(1, wait=True)
        pvs['AO:STEP:3:EN'].put(1, wait=True)
        pvs['AO:STEP:4:EN'].put(1, wait=True)

    pvs['AO:STEP:CURSOR'].put(0, wait=True)

def stream_to_disk(pvs, ssb, maxbytes=None, maxtime=None, update=True):
        """Stream data to host stop after time, bytes or flag"""
        LINE_UP = '\033[1A'
        ERASE_LINE = '\033[2K'
        bufferlen = ssb * 1024
        buffer = bytearray(bufferlen)
        byteview = memoryview(buffer).cast('B')
        print("Starting Stream")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((pvs.uut, 4210))
            with open(pvs.datafile, 'wb') as fp:
                index = 0
                tbytes = 0
                t0 = 0
                while True:
                    nbytes = sock.recv_into(byteview[index:])

                    if nbytes == 0: 
                        print('Error: uut has stoppped')
                        break

                    index += nbytes
                    tbytes += nbytes

                    if t0 == 0: t0 = time.time()

                    if index >= bufferlen:
                        if update:
                            tt = time.time() - t0
                            print(f"Streaming {int(tt)}s {(tbytes >> 20) / tt:.5f} MB/s > {pvs.datafile}")

                        fp.write(buffer[:index])
                        index = 0

                        if maxtime and time.time() - t0 > maxtime:
                            print('Stream reached max time')
                            break

                        if maxbytes and tbytes >= maxbytes:
                            print('Stream reached max bytes')
                            break

                        if pvs.stop_flag:
                            print("Stream received stop signal")
                            break

                        if update: print(LINE_UP + ERASE_LINE , end="")

                fp.flush()
            sock.shutdown(socket.SHUT_RDWR)
        print(f"{tbytes:,} bytes {tbytes // ssb:,} samples total")

def read_from_disk(filename, data_format):
    """Read data from disk and organize into dataset object"""
    dataset = DotDict()
    
    file_size = os.path.getsize(filename)
    bytes_to_read = file_size - (file_size % data_format.samp_w)
    dataset.data = np.fromfile(filename, dtype=data_format.dtype, count=bytes_to_read)

    dataset.samples = len(dataset.data)

    dataset.es_indices = find_event_signatures(dataset, data_format.samp_w)
    dataset.es_mask = np.full(dataset.samples, True)

    if len(dataset.es_indices) > 0: 
        dataset.es_mask[dataset.es_indices] = False
    else:
        print('Warning: no event signatures found')

    dataset.chan = {}
    dataset.channels = data_format.data_i
    for chan in dataset.channels:
        print(f'read_from_disk chan[{chan}]')
        id = f"chan_{chan}"
        dataset.chan[chan] = dataset.data[id][dataset.es_mask]
    dataset.datalen = len(dataset.chan[dataset.channels[0]])

    dataset.spad = {}
    for idx, _ in enumerate(data_format.spad_i):
        print(f'read_from_disk spad[{idx}]')
        id = f"spad_{idx}"
        dataset.spad[idx] = dataset.data[id]

    print(f'read_from_disk datalen: {dataset.datalen}')
    print(f'read_from_disk samples: {dataset.samples}')

    return dataset

def find_event_signatures(dataset, ssb):
    """Convert data to uint32 and look for es"""
    signatures = [
        0xaa55f151,
        0xaa55f152,
        0xaa55f154,
    ]
    if ssb % 4 != 0:
        print('Warning unable to find es as sample size is not divisble by 4')
        #TODO: trim to fit (uint8?)
        return []
    
    chans32 = ssb // 4
    data32 = dataset.data.view(np.uint32).reshape(-1, chans32).T
    for dat in data32:
        for es in signatures:
            indices = np.where(dat == es)[0]
            if len(indices) > 0:
                return indices
    return []

def multiplot(dataset, title, args, pvs):
    """Plots multiple subplots"""
    adef = [args.loopbacks, args.signal, args.validate, args.spad]
    ta = len([a for a in adef if a is not None])
    fig, axs = plt.subplots(ta, 1, figsize=(10, 5), sharex=True, )
    fig.canvas.manager.set_window_title(f"Allison Demo {title}")
    index = 0

    if args.plot_egu:
        eslo = pvs['AI:CAL:ESLO'].get()
        print(f'eslo {eslo}')
        eoff = pvs['AI:CAL:EOFF'].get()
        print(f'eoff {eoff}')
        
    if not isinstance(axs, np.ndarray): axs = [axs]

    #loopback plot
    loopbacks = adef[0]
    if loopbacks != None:
        for chan in loopbacks:
            if chan not in dataset.chan: continue
            label = f"Chan {chan}"
            print(f"Plotting AO {label}")
            raw = dataset.chan[chan]
            if args.plot_egu:
               volts = np.add(np.multiply(raw, eslo[chan]), eoff[chan])
               yy = volts
            else:
               yy = raw
            axs[index].plot(yy, label=label)
        axs[index].set_title('AO loopback')
        axs[index].legend(loc="upper left")
        axs[index].set_ylabel('V' if args.plot_egu else 'codes')
        index += 1
    
    #signal plot
    signals = adef[1]
    if signals != None:
        for chan in signals:
            if chan not in dataset.chan: continue
            label = f"Chan {chan}"
            print(f"Plotting Signal {label}")
            raw = dataset.chan[chan]
            if args.plot_egu:
               volts = np.add(np.multiply(raw, eslo[chan]), eoff[chan])
               yy = volts
            else:
               yy = raw
            axs[index].plot(yy, label=label)
        axs[index].set_title('Signal')
        axs[index].legend(loc="upper left")
        axs[index].set_ylabel('V' if args.plot_egu else 'codes')
        index += 1

    #Validation Plot
    validatees = adef[2]
    if validatees != None:

        offset = 0
        es_arr = np.full(dataset.datalen, 0)
        es_ajust = np.arange(0, len(dataset.es_indices))
        es_arr[dataset.es_indices - es_ajust] = 1

        for chan in validatees:
            if chan not in dataset.chan: continue
            transitions = find_step_transitions(dataset.chan[chan], dataset.threshold)
            trans_arr = np.full(dataset.datalen, 0)
            trans_arr[0] = 1
            trans_arr[transitions] = 1

            print(f"Plotting Validation chan {chan}")
            axs[index].plot(es_arr + offset, label=f"es {chan}")
            offset += 1
            axs[index].plot(trans_arr + offset, label=f"transitions {chan}")
            offset += 1
            axs[index].plot((trans_arr ^ es_arr) + offset, label=f"ERROR (xor) {chan}", color="red")
            offset += 1

        axs[index].set_title('Validation')
        axs[index].legend(loc="upper left")
        index += 1

    #Spad plot
    spads = adef[3]
    if spads != None:
        for chan in spads:
            if chan not in dataset.spad: continue
            label = f"Spad {chan}"
            print(f"Plotting {label}")
            axs[index].plot(dataset.spad[chan], label=label)
        axs[index].set_title('Spad')
        axs[index].legend(loc="upper left")
        index += 1

def slow_plt(chans, data, burstlen):
    """Plot first value of each burst"""
    plt.figure('Slow plot')
    for chan in chans:
        if chan not in data: continue
        print(f"Slow plotting Chan {chan}")
        plt.plot(data[chan][0::burstlen], label=f"chan {chan}")
    plt.legend(loc="upper left")

def stack_plt(chans, data, burstlen, offset=0):
    """Plot each burst stacked"""
    for chan in chans:
        if chan not in data: continue
        cursor = 0
        datalen = len(data[chan])
        plt.figure(f"Stack plot Chan {chan}")
        print(f"Stack plotting Chan {chan}")
        while cursor + burstlen <= datalen:
            plt.plot(data[chan][cursor: cursor + burstlen] + (cursor // burstlen) * offset) #fix me 
            cursor += burstlen

def find_step_transitions(data, threshold):
    """checks the array for steps exceeding threshold"""
    diffs = np.diff(data)
    return np.where(np.abs(diffs) > threshold)[0] + 1

def find_unique_es_intervals(dataset):
    if len(dataset.es_indices) > 0:
        unique_es_diffs = np.unique(np.diff(dataset.es_indices))
        print(f"Unique event signature intervals {len(dataset.es_indices)} {unique_es_diffs}")


# Starts here

def run_main(args):
    pvs = PVHelper(args.uut, args.ao_site, args.trace)
    mask = MaskHelper(args.mask)

    args.maxtime = None if args.maxbytes else args.maxtime
    
    pvs['STREAM_SUBSET_MASK'].put(mask.hex, wait=True)
    if args.translen: pvs['RTM_TRANSLEN'].put(args.translen, wait=True)

    #monitor cursor and stop when complete
    def cursor_callback(value, **kwargs):
        if value >= args.scan_steps and pvs.cstate != 0:
            print('Requesting stop')
            pvs.stop_flag = True

    epics.PV(f"{args.uut}:0:AO:STEP:CURSOR", callback=cursor_callback, auto_monitor=True)

    #Generate data format dtype
    nchan = int(pvs['NCHAN'].get())
    chanlen = 4 if int(pvs['data32'].get()) else 2
    spadlen = int(pvs['SPAD:LEN:r'].get())
    trigger_rate = pvs['SIG:TRG_EXT:FREQ'].get()
    data_format = get_data_format(nchan, chanlen, spadlen, mask.list)

    #Setup ramp 
    setup_ramp(pvs, args.amplitude, args.scan_steps, args.ao_step_en)

    #stream data to disk then read in data
    if args.stream:
        stream_to_disk(pvs, data_format.samp_w, maxtime=args.maxtime, maxbytes=args.maxbytes)
    dataset = read_from_disk(pvs.datafile, data_format)

    find_unique_es_intervals(dataset)

    burstlen = int(pvs['RTM_TRANSLEN'].get()) - 1

    #plotting here

    if args.multiplot:
        title = f"{args.uut} {trigger_rate}Hz"
        dataset.threshold = args.threshold
        multiplot(dataset, title, args, pvs)

    if args.slow != None:
        slow_plt(args.slow, dataset.chan, burstlen)

    if args.stack != None:
        stack_plt(args.stack, dataset.chan, burstlen)
    
    plt.tight_layout()
    plt.show()


# Argparser

def list_of_channels(arg):
    if arg.lower() == 'none': return None
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
    parser = argparse.ArgumentParser(description="Allison Plotter")

    parser.add_argument('--loopbacks', default='1-4', type=list_of_channels, help="loopback channels to plot")
    parser.add_argument('--signal', default='5,6', type=list_of_channels, help="Signal channels to plot")
    parser.add_argument('--validate', default='1', type=list_of_channels, help="Validate channel to plot")
    parser.add_argument('--spad', default=None, type=list_of_channels, help="Spad channels to plot")

    parser.add_argument('--stream', default=1, type=int, help="to stream or not to stream")
    
    parser.add_argument('--maxtime', default=None, type=int, help="Stream max time")
    parser.add_argument('--maxbytes', default=None, type=int, help="Stream max bytes")

    parser.add_argument('--stack', default='none', type=list_of_channels, help="channels to stack plot")
    parser.add_argument('--slow', default='none', type=list_of_channels, help="channels to slow plot")
    parser.add_argument('--multiplot', default=1, type=int, help="multiplot")
    parser.add_argument('--plot_egu', default=0, type=int, help="[0]: plot codes, 1: plot volts")

    parser.add_argument('--scan_steps', default=500, type=int, help="Ramp scan_steps")
    parser.add_argument('--amplitude', default=10, type=int, help="Ramp amplitude")
    parser.add_argument('--ao_site', default=5, type=int, help="Site with the ao")
    parser.add_argument('--ao_step_en', default=1, type=int, help="Enable DAC ramps (almost always want this)")
    parser.add_argument('--translen', default=None, type=valid_translen, help="Burst length: any number 1024 - 22000")
    parser.add_argument('--mask', default="1-6,17-20", type=list_of_channels, help="channels in the mask")
    parser.add_argument('--threshold', default=20, type=int, help="Jump index threshold value (eg 20 codes)")
    parser.add_argument('--trace', default=0, type=int, help="print epics trace")

    parser.add_argument('uut', help="uut name")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
