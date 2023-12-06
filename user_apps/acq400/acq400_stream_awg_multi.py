#!/usr/bin/env python3

"""Stream data from FILE continuously to UUT stream_awg port"""


import acq400_hapi
from acq400_hapi import timing
from acq400_hapi import awg_data
from acq400_hapi import netclient as netclient
import argparse
import sys
import threading
import os
import time



def read(file):
    with open(file, "rb") as fd:
        return fd.read()
    
NBUFS = 0
IBUF = 0

# monitor
BCOUNT = 0
BSIZE  = 0


@timing
def load_awg_top(args):
    global NBUFS, BCOUNT, BSIZE
    uut = acq400_hapi.Acq400(args.uuts[0])
    trigger = args.soft_trigger

    
    bufs = [ read(f) for f in args.file.split(",") ] 
    NBUFS = len(bufs)
    
    with netclient.Netclient(uut.uut, acq400_hapi.AcqPorts.AWG_STREAM) as nc:
        while True:
            nc.sock.send(bufs[IBUF])
            if trigger:
                uut.s0.soft_trigger = 1
                trigger = 0
            BCOUNT += 1
            BSIZE = len(bufs[IBUF])
    
def buffer_changer():
    global IBUF
    while True:
        cc = sys.stdin.read(1)
        if "0123456789".find(cc) >= 0:
            ix = int(cc)            
            if ix >= 0 and ix < NBUFS:
                IBUF = ix
                
def monitor():
    global IBUF, NBUFS, BCOUNT, BSIZE
    bc = BCOUNT
    
    while True:
        time.sleep(1)
        print("\rix {} NBUFS {} rate: {} MB/s >".format(IBUF, NBUFS, (BCOUNT-bc)*BSIZE/0x100000), end="")
        bc = BCOUNT

def get_parser():
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default=None, help="file to load")
    parser.add_argument('--soft_trigger', default=0, type=int, help='Emit soft trigger')        
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser


def run_main(args):
    threading.Thread(target=buffer_changer).start()
    threading.Thread(target=monitor).start()
    load_awg_top(args)

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())