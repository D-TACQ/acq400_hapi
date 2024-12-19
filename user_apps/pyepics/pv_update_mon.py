#!/usr/bin/env python3

"""Monitors a set of pvs for mean, max and min update rate and alerts if above a threshold"""

import argparse
import epics
import time
from acq400_hapi import acq400_logger, pprint
import sys
import numpy as np
from npy_append_array import NpyAppendArray

log = acq400_logger("pv_update_mon", logfile="pv_update_mon.log")

class UpdateMonitor:

    def __init__(self, uut, pvs, threshold):

        self.pvs = {}
        self.threshold = threshold
        self.dt = []
        self.updates = 0

        for pvname in pvs:
            pvname = pvname.format(uut=uut)
            log.info(f"Monitoring {pvname}")
            if pvname in self.pvs: continue
            pv = epics.PV(pvname, auto_monitor=True)
            pv.add_callback(self.callback)
            self.pvs[pvname] = DotDict()
            self.pvs[pvname].pv = pv
            self.pvs[pvname].ready = False

        while not all(pv.connected for pv.pv in self.pvs):
            time.sleep(1)
        print("all connected")

    def callback(self, pvname=None, timestamp=None, **kwargs):
        if 'timestamp' not in self.pvs[pvname]:
            self.pvs[pvname].timestamp = timestamp
            self.pvs[pvname].sum = 0
            self.pvs[pvname].total = 0
            self.pvs[pvname].errors = 0
            self.last_time = self.pvs[pvname].timestamp
            return
        
        diff = timestamp - self.pvs[pvname].timestamp
        self.dt.append(timestamp - self.last_time)
        self.last_time = timestamp
        self.updates += 1
        if self.updates > 10:
            with NpyAppendArray('data.npy') as npaa:
                npaa.append(np.array(self.dt))
            self.dt = []
            self.updates = 0

        if "max" not in self.pvs[pvname]:
            self.pvs[pvname].min = diff
            self.pvs[pvname].max = diff

        self.pvs[pvname].total += 1
        self.pvs[pvname].sum += diff

        if diff > self.pvs[pvname].max:
            self.pvs[pvname].max = diff

        if diff < self.pvs[pvname].min:
            self.pvs[pvname].min = diff

        if diff > self.threshold:
            log.error(f"{pvname} {timestamp} {diff} diff is above threshold ")
            self.pvs[pvname].errors += 1

        if self.pvs[pvname].timestamp == timestamp:
            log.error(f"{pvname} {timestamp} timestamps are the same")
            self.pvs[pvname].errors += 1

        self.pvs[pvname].timestamp = timestamp
        self.pvs[pvname].ready = True

class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

def run_main(args):
    um = UpdateMonitor(args.uut, args.pvs, args.threshold)

    try:
        t0 = time.time()
        LINE_UP = '\033[1A'
        ERASE_LINE = '\033[2K'

        while True:
            lines = 1
            print(f"Update Mon Threshold {args.threshold}s Runtime {time.time() - t0:.0f}s")
            for pvname, stats in um.pvs.items():
                if not stats.ready: continue
                lines += 1
                print(f"pv {pvname} updates {stats.total} mean {stats.sum / stats.total:.3f} max {stats.max:.3f} min {stats.min:.3f} errors {stats.errors} timestamp {stats.timestamp}")

            time.sleep(0.2)
            print((LINE_UP + ERASE_LINE) * lines, end="")
            
    except KeyboardInterrupt:
        pass

    for pvname, stats in um.pvs.items():
        log.info(pvname)
        log.info(pprint(stats, to_string=True))

def list_of_strings(arg):
    return arg.split(',')

def get_parser():
    parser = argparse.ArgumentParser(description="monitors pv update rate")
    parser.add_argument('--pvs', default="{uut}:1:AI:WF:01:V.VALA", type=list_of_strings, help="pvs to monitor (comma seperated)")
    parser.add_argument('--threshold', default=1.5, type=float, help="update error threshold")
    parser.add_argument('uut', help="uut name")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

