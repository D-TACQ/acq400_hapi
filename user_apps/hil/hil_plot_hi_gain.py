#!/usr/bin/env python

""" hil_plot_hi_gain Use ADC readback to adjust DAC output

    - Hardware In Loop : Hi Gain. Trim AO's until measured loopback is zero 
    - upload to AWG and optionally run a capture.
    - data for upload is either File (host-local data file) or Rainbow, a test pattern, 
         assumes that clocking has been pre-assigned.

usage::

    hil_plot_hi_gain.py [-h] [--gain GAIN] [--files FILES] [--loop LOOP]
                           [--store STORE] [--nchan NCHAN] [--awglen AWGLEN]
                           [--ao0 AO0] [--passvalue PASSVALUE]
                           [--aochan AOCHAN] [--post POST] [--trg TRG]
                           [--plot PLOT] [--wait_user WAIT_USER]
                           [--set_volts SET_VOLTS]
                           [--transfer_function TRANSFER_FUNCTION]
                           uuts

acq1001 HIL zero offset demo

positional arguments:
  uuts                  uut

optional arguments:
  -h, --help            show this help message and exit
  --gain GAIN           set gain constant
  --files FILES         list of files to load
  --loop LOOP           loop count
  --store STORE         save data when true
  --nchan NCHAN         channel count for pattern
  --awglen AWGLEN       samples in AWG waveform
  --ao0 AO0             first ao in set
  --passvalue PASSVALUE
                        acceptable error
  --aochan AOCHAN       AO channel count, if different to AI (it happens)
  --post POST           samples in ADC waveform
  --trg TRG             trg "int|ext rising|falling"
  --plot PLOT           --plot 1 : plot data, 2: persistent
  --wait_user WAIT_USER
                        1: force user input each shot
  --set_volts SET_VOLTS
                        list of voltages to converge to
  --transfer_function TRANSFER_FUNCTION
                        generate transfer fun, step size in V

"""

import sys
import acq400_hapi
import argparse
import numpy as np
import matplotlib.pyplot as plt
import hil_plot_support as pltsup
import zero_offset
from future import builtins
from builtins import input


def run_target(uut, args):
    args.plot_volts = True if args.set_volts != None else False
    work = zero_offset.ZeroOffset(uut, args.nchan, args.awglen,
                               target=(args.set_volts if args.plot_volts else 0),
                               aochan = int(args.aochan), 
                               gain = args.gain*(0.95*32768/10 if args.plot_volts else 1),
                               passvalue = args.passvalue, ao0 = args.ao0) 
    try:
        loader = work.load()
        ii = 0
        while next(loader):        
            uut.run_oneshot()        
            print("read_chan %d" % (args.post*args.nchan))
            rdata = uut.read_chan(0, args.post*args.nchan)                        
            if args.plot > 0:
                plt.cla()
                title = "AI for shot %d %s" % (ii, "persistent plot" if args.plot > 1 else "")
                print(title)
                plt.title(title)
                pltsup.plot(uut, args, ii, rdata)               
                pltsup.store_file(ii, rdata, args.nchan, args.post)
                if args.wait_user:
                    key = input("hit return to continue, q for quit").strip()
                    if key == 'q':
                        work.user_quit = True
                        if work.in_bounds:
                            work.finished = True
                    print("raw_input {}".format(key))
                else:
                    if work.in_bounds:
                        work.finished = True


                chx = np.reshape(uut.scale_raw(rdata, volts=args.plot_volts), (args.post, args.nchan))
                if args.plot_volts:
                    chv = np.array([ uut.chan2volts(ch+1, chx[:,ch]) for ch in range(0, args.nchan)])
                    print("feedback volts")
                    work.feedback(np.transpose(chv))
                else:
                    work.feedback(chx)
                ii += 1
    except StopIteration:
        print("offset zeroed within bounds")
    except acq400_hapi.acq400.Acq400.AwgBusyError:
        print("AwgBusyError, trying a soft trigger and quit, then re-run me")
        uut.s0.soft_trigger = '1'
        raise SystemExit
    return work


def run_transfer_function(uut, args):
    targets = np.arange(-10, 10, args.transfer_function, dtype=float)
    tf = []
    for t in np.nditer(targets):
        print("Target set {}".format(t))
        args.set_volts = t
        w = run_target(uut, args)
        tf.append(np.append([t], w.newset)) # Maybe needs to be indented? Reason for only final line saved?

    np.savetxt("transfer_function.csv", np.array(tf), fmt="%6d", delimiter=',')


def run_shots(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    acq400_hapi.cleanup.init()
    if args.plot:
        plt.ion()

    uut.s0.transient = 'POST=%d SOFT_TRIGGER=%d DEMUX=%d' % \
        (args.post, 1 if args.trg == 'int' else 0, 1 if args.store == 0 else 0)

    for sx in uut.modules:
        uut.modules[sx].trg = '1,1,1' if args.trg == 'int' else '1,0,1'

    if args.transfer_function:
        run_transfer_function(uut, args)
    else:
        run_target(uut, args)


def run_main():
    parser = argparse.ArgumentParser(description='acq1001 HIL zero offset demo')
    parser.add_argument('--gain', type=float, default=0.1, help="set gain constant")
    parser.add_argument('--files', default="", help="list of files to load")
    parser.add_argument('--loop', type=int, default=1, help="loop count")        
    parser.add_argument('--store', type=int, default=1, help="save data when true") 
    parser.add_argument('--nchan', type=int, default=32, help='channel count for pattern')    
    parser.add_argument('--awglen', type=int, default=2048, help='samples in AWG waveform')
    parser.add_argument('--ao0', type=int, default=0, help='first ao in set')
    parser.add_argument('--passvalue', type=float, default=1, help='acceptable error')
    parser.add_argument('--aochan', type=int, default=0, help='AO channel count, if different to AI (it happens)')
    parser.add_argument('--post', type=int, default=100000, help='samples in ADC waveform')
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('--plot', type=int, default=1, help='--plot 1 : plot data, 2: persistent')
    parser.add_argument('--wait_user', type=int, default=0, help='1: force user input each shot')
    parser.add_argument('--set_volts', default=None, help='list of voltages to converge to')
    parser.add_argument('--transfer_function', default=0, type=float, help='generate transfer fun, step size in V')
    parser.add_argument('uuts', nargs=1, help="uut ")
    run_shots(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()

