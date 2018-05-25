#!/usr/bin/env python

""" hil_plot Hardware In Loop : load AO data,run a shot, get AI data, plot, repeat.

    - upload to AWG and optionally run a capture.
    - data for upload is either File (host-local data file) or Rainbow, a test pattern.
    - assumes that clocking has been pre-assigned.

usage:: 

    hil_plot.py [-h] [--autorearm AUTOREARM] [--is_debug IS_DEBUG]
                   [--files FILES] [--pulse PULSE] [--loop LOOP]
                   [--range RANGE] [--store STORE] [--nchan NCHAN]
                   [--aochan AOCHAN] [--awglen AWGLEN] [--post POST]
                   [--trg TRG] [--plot PLOT] [--plot_volts PLOT_VOLTS]
                   [--wait_user WAIT_USER]
                   uuts

acq1001 HIL demo

positional arguments:
  uuts                  uut

optional arguments:
  -h, --help            show this help message and exit
  --autorearm AUTOREARM     load the waveform once, repeat many
  --is_debug IS_DEBUG       set debug level
  --files FILES         list of files to load
  --pulse PULSE         interval,duration,scan: + : each channel in turn
  --loop LOOP           loop count
  --range RANGE         set range on ADC
  --store STORE         save data when true
  --nchan NCHAN         channel count for pattern
  --aochan AOCHAN       AO channel count, if different to AI (it happens)
  --awglen AWGLEN       samples in AWG waveform
  --post POST           samples in ADC waveform
  --trg TRG             trg "int|ext rising|falling"
  --plot PLOT           --plot 1 : plot data, 2: persistent
  --plot_volts PLOT_VOLTS
                        1: plot values in volts
  --wait_user WAIT_USER
                        1: force user input each shot


"""
import sys
import acq400_hapi
from acq400_hapi import awg_data
import argparse
import numpy as np
import matplotlib.pyplot as plt
import hil_plot_support as pltsup
import os
import subprocess

import hil_plot_support as pltsup
from future import builtins
from builtins import input


def run_shots(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    acq400_hapi.cleanup.init()
    if args.plot:
        plt.ion()

    uut.s0.transient = 'POST=%d SOFT_TRIGGER=%d DEMUX=0' % \
        (args.post, 1 if args.trg == 'int' else 0) 

    if args.aochan == 0:
        args.aochan = args.nchan

    for sx in uut.modules:
        if args.trg == 'int':
            uut.modules[sx].trg = '1,1,1'
        else:
            if args.trg.contains('falling'):
                uut.modules[sx].trg = '1,0,0'
            else:
                uut.modules[sx].trg = '1,0,1'
                
    if args.pulse != None:
        work = awg_data.Pulse(uut, args.aochan, args.awglen, args.pulse.split(','))
    elif args.files != "":
        work = awg_data.RunsFiles(uut, args.files.split(','), run_forever=True)
    else:
        work = awg_data.RainbowGen(uut, args.aochan, args.awglen, run_forever=True)
        # compensate gain ONLY Rainbow Case
        if args.range != "default":
            gain = 10/float(args.range.strip('V'))
            print("setting work.gain {}".format(gain))
            work.gain = gain

    # Set range knobs, valid ALL data sources.
    if args.range != "default":
        for sx in uut.modules:
            print("setting GAIN_ALL {}".format(args.range))
            uut.modules[sx].GAIN_ALL = args.range
            break

    print("args.autorearm {}".format(args.autorearm))

    loader = work.load(autorearm = args.autorearm)
    for ii in range(0, args.loop):
        print("shot: %d" % (ii))
        if ii == 0 or not args.autorearm:
            f = next(loader)
            print("Loaded %s" % (f))
        else:
            if args.autorearm and ii+1 == args.loop:
            # on the final run, drop out of autorearm mode. 
            # the final shot MUST be in ONCE mode so that the DMAC
            # is freed on conclusion
                for sx in uut.modules:
                    if uut.modules[sx].MODEL.startswith('AO'):
                        uut.modules[sx].playloop_oneshot = '1'
                        
        uut.run_oneshot()

        print("read_chan %d" % (args.post*args.nchan))
        rdata = uut.read_chan(0, args.post*args.nchan)
        if args.store:
            pltsup.store_file(ii, rdata, args.nchan, args.post)
        if args.plot > 0 :
            plt.cla()
            plt.title("AI for shot %d %s" % (ii, "persistent plot" if args.plot > 1 else ""))
            pltsup.plot(uut, args, ii, rdata)
        if args.wait_user is not None:
            input("hit return to continue")


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

class ExecFile:
    def __init__(self, fname):
        self.fname = fname
    def __call__(self):
        args = [self.fname, pltsup.current_file]
        print("subprocess.call({})".format(args))
        subprocess.call(args, stdout=sys.stdout, shell=False)

class Integer:
    def __init__(self, value):
        self.value = int(value)
    def __call__(self):
        return self.value

class Prompt:
    def __call__(self):
        input("hit return to continue")              


def select_prompt_or_exec(value):
    if is_exe(value):
        return ExecFile(value)
    else:
        if int(value) == 1:
            return Prompt()

def run_main():
    parser = argparse.ArgumentParser(description='acq1001 HIL demo')
    # --type=bool does not work, try this: 
    # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    parser.add_argument('--autorearm', default=False, type=lambda x: (str(x).lower() in ['true', 't', 'yes', '1']), 
                        help="load the waveform once, repeat many")
    parser.add_argument('--is_debug', default=False, type=lambda x: (str(x).lower() in ['true', 't', 'yes', '1'])),
    parser.add_argument('--files', default="", help="list of files to load")
    parser.add_argument('--pulse', help="interval,duration,scan: + : each channel in turn")
    parser.add_argument('--loop', type=int, default=1, help="loop count")
    parser.add_argument('--range', default="default", help="set range on ADC")
    parser.add_argument('--store', type=int, default=1, help="save data when true") 
    parser.add_argument('--nchan', type=int, default=32, help='channel count for pattern')
    parser.add_argument('--aochan', type=int, default=0, help='AO channel count, if different to AI (it happens)')
    parser.add_argument('--awglen', type=int, default=2048, help='samples in AWG waveform')
    parser.add_argument('--post', type=int, default=100000, help='samples in ADC waveform')
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('--plot', type=int, default=1, help='--plot 1 : plot data, 2: persistent')
    parser.add_argument('--plot_volts', type=int, default=0, help='1: plot values in volts')
    parser.add_argument('--wait_user', type=select_prompt_or_exec, default=0, help='1: force user input each shot')
    parser.add_argument('uuts', nargs=1, help="uut ")
    run_shots(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()

