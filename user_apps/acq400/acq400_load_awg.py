#!/usr/bin/env python3

"""
upload file to AWG for a one-shot play
data for upload is a single file
assumes that clocking has been pre-assigned.


positional arguments:
  uuts               uut

optional arguments:
  -h, --help         show this help message and exit
  --files FILES      list of files to load
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
    args.shot = uut.modules[args.aosite].shot
    if args.mode == 1 or (args.mode == 2 and rep == 0):
        acq400_hapi.Acq400UI.exec_args_playtrg(uut, args)
        loaded = 0
 
        while loaded != 1:
            try:
                with open(args.file, "rb") as fd:
                    uut.load_awg(file_extender(fd, args.awg_extend), autorearm=args.mode==2)
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
               
    if args.soft_trigger:
        uut.s0.soft_trigger = '1'

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
        if args.reps > 1:
            wait_completion(args, uut)
    print("playloop_length {}".format(uut.modules[args.aosite].playloop_length))


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default="", help="file to load")
    parser.add_argument('--mode', default=2, type=int, help="mode: 1 oneshot, 2 oneshot_autorearm")
    parser.add_argument('--awg_extend', default=1, type=int, help='Number of times the AWG is repeated.')
    parser.add_argument('--soft_trigger', default=1, type=int, help='Emit soft trigger')
    parser.add_argument('--reps', default=1, type=int, help='Repetitions')
    parser.add_argument('--aosite', default=1, type=int, help='Site of AO module')
    acq400_hapi.Acq400UI.add_argument_playtrg(parser)
    parser.add_argument('uuts', nargs=1, help="uut ")
    return parser.parse_args(argStr)


def run_main():
    load_awg_top(get_args())

# execution starts here

if __name__ == '__main__':
    run_main()
