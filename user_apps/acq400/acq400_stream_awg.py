#!/usr/bin/env python3

"""
acq400_stream_awg.py --file FILE UUT

Stream data from FILE continuously to UUT stream_awg port

"""


import acq400_hapi
from acq400_hapi import timing
from acq400_hapi import awg_data
from acq400_hapi import netclient as netclient
import argparse

@timing
def load_awg_top(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    trigger = args.soft_trigger
    
    with open(args.file, "rb") as fd:
        buf = fd.read()
     
    with netclient.Netclient(uut.uut, acq400_hapi.AcqPorts.AWG_STREAM) as nc:
        while True:
            nc.sock.send(buf)
            if trigger:
                uut.s0.soft_trigger = 1
                trigger = 0
            
            
            
    print("Hello World")

def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default=None, help="file to load")
    parser.add_argument('--soft_trigger', default=0, type=int, help='Emit soft trigger')        
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser.parse_args(argStr)


def run_main():
    load_awg_top(get_args())

# execution starts here

if __name__ == '__main__':
    run_main()    