#!/usr/bin/env python

""" acq480 controls .. set ACQ480 parameters
    acq480 controls [opts] UUT1 [UUT2 ..]
    where UUT1 is the ip-address or host name of first uut
    example test client runs captures in a loop on one or more uuts

"""

import sys
import acq400_hapi
import argparse


ALL = 0


def set_T50R(module, enable, channel):
    if channel == ALL:
        module.set_knob("T50R", enable)
    else:
        module.set_knob("TR50R_{:d}".format(channel), enable)
   
def set_gain(module, gain, channel):
    chans = range(1,9) if channel == ALL else channel
    
    for ch in chans:
        module.set_knob("ACQ480_GAIN_{:02d}".format(ch), gain)
    
def set_480_uut(uut, args):
    if args.FIR:
        uut.modules[1].ACQ480_FIR_01 = args.FIR
      
    sl =  uut.modules if args.site == ALL else [args.site]
    
    for s in sl:
        if args.T50R != None:
            set_T50R(uut.modules[s], args.T50R, args.channel)
        if args.GAIN != None:
            set_gain(uut.modules[s], args.GAIN, args.channel)
        
        
def set_480(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for u in uuts:
        set_480_uut(u, args)

# execution starts here

def run_main():
    parser = argparse.ArgumentParser(description='configure acq480')
    parser.add_argument('--FIR', default=None, type=str)
    parser.add_argument('--T50R', default=None, type=int)
    parser.add_argument('--GAIN', default=None, type=int)
    parser.add_argument('--site', default=ALL, type=int)
    parser.add_argument('--channel', default=ALL, type=int)
    parser.add_argument('uuts', nargs='+', help='uut1 [uut2..]')
    set_480(parser.parse_args())

if __name__ == '__main__':
    run_main()




