#!/usr/bin/env python3

"""upload file to AWG for a one-shot play

data for upload is a single file
assumes that clocking has been pre-assigned.

load awg simplest

positional arguments:
  uuts                  uut

options:
  -h, --help            show this help message and exit
  --file FILE           file to load
  --mode MODE           mode: 1 oneshot, 2 oneshot_autorearm
  --awg_extend AWG_EXTEND
                        Number of times the AWG is repeated.
  --soft_trigger SOFT_TRIGGER
                        Emit soft trigger
  --reps REPS           Repetitions
  --port PORT           optional port number for fast start server
  --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG             int|ext,rising|falling
  --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE         1 : enable command tracing
  --auto_soft_trigger AUTO_SOFT_TRIGGER
                        force soft trigger generation
  --clear_counters      clear all counters SLOW
  --playtrg PLAYTRG     int|ext,rising|falling
  --aosite AOSITE       Site of AO module
  --playdiv PLAYDIV     CLKDIV for play site

"""

import sys
import socket

import acq400_hapi
from acq400_hapi import awg_data
from acq400_hapi import netclient as netclient
import argparse


from functools import wraps
from time import time
from time import sleep

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('....TIMING:func:%r took: %2.2f sec' % (f.__name__, te-ts))
        return result
    return wrap


def file_extender(fd, ext_count):
    buf = fd.read()
    buf0 = buf

    while ext_count > 1:
        buf += buf0
        ext_count -= 1
        
    return buf
        

@timing
def load_awg(args, uut, rep):
    acq400_hapi.Acq400UI.exec_args(uut, args)
    args.shot = uut.modules[args.aosite].shot
    if args.mode == 1 or (args.mode == 2 and rep == 0):
        
        loaded = 0
 
        while loaded != 1:
            try:
                with open(args.file, "rb") as fd:
                    uut.load_awg(file_extender(fd, args.awg_extend), autorearm=args.mode==2, port=args.port)
                    loaded = 1
            except Exception as e:
                if loaded == 0:
                    print("First time: caught {}, abort and retry".format(e))
                    loaded = -1
                    uut.modules[args.aosite].playloop_oneshot = '1'
                    uut.modules[args.aosite].awg_abort = '1'
                    sleep(0.1)
                else:
                    print("Retry failed: caught {} FAIL".format(e))
                    exit(1)

@timing
def wait_completion(args, uut):
   if args.mode == 1:
       while uut.modules[args.aosite].task_active == '1' or  uut.modules[args.aosite].completed_shot == '0':
           sleep(0.1)
       # print("polling completion")
   if args.mode == 2:
       while args.shot == uut.modules[args.aosite].shot:
           sleep(0.1)

@timing
def load_awg_top(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    for rep in range(0, args.reps):
        if rep > 0:
            print("rep {}".format(rep))
        load_awg(args, uut, rep)
        if args.soft_trigger:
            if args.port is not None:
                while acq400_hapi.intpv(uut.s1.AWG_ARM) == 0:
                    sleep(0.1)
            uut.s0.soft_trigger = '1'
        if args.reps > 1:
            wait_completion(args, uut)
    print("playloop_length {}".format(uut.modules[args.aosite].playloop_length))


def get_parser():
    parser = argparse.ArgumentParser(description='load awg simplest')
    parser.add_argument('--file', default="", help="file to load")
    parser.add_argument('--mode', default=2, type=int, help="mode: 1 oneshot, 2 oneshot_autorearm")
    parser.add_argument('--awg_extend', default=1, type=int, help='Number of times the AWG is repeated.')
    parser.add_argument('--soft_trigger', default=1, type=int, help='Emit soft trigger')
    parser.add_argument('--reps', default=1, type=int, help='Repetitions')
    parser.add_argument('--port', default=None, type=int, help='optional port number for fast start server')
    acq400_hapi.Acq400UI.add_args(parser, play=True)
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser

# execution starts here

if __name__ == '__main__':
    load_awg_top(get_parser().parse_args())
