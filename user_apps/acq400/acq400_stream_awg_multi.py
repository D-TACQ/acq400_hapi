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
import sys
import threading
import os
import time



def read(file):
    with open(file, "rb") as fd:
        return fd.read()
    
NBUFS = 0
IBUF = 0


@timing
def load_awg_top(args):
    global NBUFS
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
                
    print("Hello World")
    
def buffer_changer():
    global IBUF
    while True:
        cc = sys.stdin.read(1)
        if "0123456789".find(cc) >= 0:
            ix = int(cc)
            print("ix {} NBUFS {}".format(ix, NBUFS))
            if ix >= 0 and ix < NBUFS:
                IBUF = ix

def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default=None, help="file to load")
    parser.add_argument('--soft_trigger', default=0, type=int, help='Emit soft trigger')        
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser.parse_args(argStr)


def run_main(args):
    threading.Thread(target=buffer_changer).start()
    load_awg_top(args)
    while True:
        time.sleep(1)
        print("IBUF {}".format(IBUF))

# execution starts here

if __name__ == '__main__':
    run_main(get_args())    