#!/usr/bin/env python3

"""

acq400_upload.py :: simplified upload-only program.

For fullshot capture and upload, see acq400_fullshot.py 

example: upload data from previous "DEMUX=0" shot:
[pgm@hoy5 acq400_hapi]$ ./user_apps/acq400/acq400_upload.py --save_data BOLO --trace_upload 1 acq2106_123
INFO: Shotcontroller.handle_data() acq2106_123 data valid: UNKNOWN
TIMING:func:'handle_data' took: 11.63 sec
RAW DATA BOLO/acq2106_123_CH00 size 19200000
TIMING:func:'upload' took: 23.67 sec
TIMING:func:'run_main' took: 23.67 sec
[pgm@hoy5 acq400_hapi]$ ls -l BOLO
BOLO/        BOLO_README  
[pgm@hoy5 acq400_hapi]$ ls -l BOLO/
acq2106_123_CH00  format            
[pgm@hoy5 acq400_hapi]$ ls -l BOLO/acq2106_123_CH00 
-rw-r--r-- 1 pgm pgm 19200000 Jul  2 20:27 BOLO/acq2106_123_CH00


"""

import sys
import acq400_hapi
import numpy as np

import os
import errno
import argparse
import re
import time

from subprocess import call

class TimedShotController(acq400_hapi.ShotControllerWithDataHandler):
    @acq400_hapi.timing
    def handle_data(self, args):
        return super().handle_data(args)

    def __init__(self, _uuts, args, shot=None):
         super().__init__(_uuts, args, shot)
      
@acq400_hapi.timing
def upload(args, doClose=False):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    #[ acq400_hapi.Acq400UI.exec_args(uut, args) for uut in uuts ]
 
    shot_controller = TimedShotController(uuts, args)
    shot_controller.handle_data(args)
    for u in uuts:  
        u.read_chan(0)
        rawfn = "{}/{}_CH00".format(args.save_data, u.uut)              
        print("RAW DATA {} size {}".format(rawfn, os.stat(rawfn).st_size))
            
    if doClose:
        for u in uuts:
            u.close()

def uniq(inp):
    out = []
    for x in inp:
        if x not in out:
            out.append(x)
    return out


def get_parser(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 upload')
    acq400_hapi.ShotControllerUI.add_args(parser)
    parser.add_argument('uuts', nargs = '+', help="uut[s]")
    return parser

@acq400_hapi.timing
def run_main(args):    
    # deduplicate (yes, some non-optimal apps call with duplicated uuts, wastes time)
    args.uuts = uniq(args.uuts)
    # encourage single ints to become a list
    if re.search(r'^\d$', args.channels) is not None:
        args.channels += ','

    upload(args)

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())
