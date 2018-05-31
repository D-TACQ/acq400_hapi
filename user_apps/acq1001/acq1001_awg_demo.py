#!/usr/bin/env python

"""
upload to AWG and optionally run a capture.
data for upload is either File (host-local data file) or Rainbow, a test pattern.
assumes that clocking has been pre-assigned.

usage: acq1001_awg_demo.py [-h] [--files FILES] [--loop LOOP]
                           [--capture CAPTURE] [--nchan NCHAN]
                           [--awglen AWGLEN] [--post POST] [--trg TRG]
                           uuts

acq1001 awg demo

positional arguments:
  uuts               uut

optional arguments:
  -h, --help         show this help message and exit
  --files FILES      list of files to load
  --loop LOOP        loop count
  --capture CAPTURE  run a capture (assumes ADC present)
  --nchan NCHAN      channel count for pattern
  --awglen AWGLEN    samples in AWG waveform
  --post POST        samples in ADC waveform
  --trg TRG          trg "int|ext rising|falling"
"""



import sys
import acq400_hapi
from acq400_hapi import awg_data
import argparse
from future import builtins
from builtins import input

        
def run_shots(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    acq400_hapi.cleanup.init()
    if args.capture > 0:
        uut.s0.transient = 'POST=%d SOFT_TRIGGER=%d' % \
            (args.post, 1 if args.trg == 'int' else 0)
        shot_controller = acq400_hapi.ShotController([uut])
    
    for sx in uut.modules:
        uut.modules[sx].trg = '1,1,1'  if args.trg == 'int' else '1,0,1'

    if args.files == "@ALLFULLSCALE":
        work = awg_data.AllFullScale(uut, args.nchan, args.awglen)    
    elif args.files != "":
        work = awg_data.RunsFiles(uut, args.files.split(','))
    else:
        work = awg_data.RainbowGen(uut, args.nchan, args.awglen)
        
    for ii in range(0, args.loop):
        print("shot: %d" % (ii))
            
        for f in work.load():
            print("Loaded %s" % (f))
            if args.capture > 0:
                shot_controller.run_shot(soft_trigger= True if args.trg=='int' else False)
            else:
                input("hit return when done")
            

def run_main():
    parser = argparse.ArgumentParser(description='acq1001 awg demo')
    parser.add_argument('--files', default="", help="list of files to load")
    parser.add_argument('--loop', type=int, default=1, help="loop count")
    parser.add_argument('--capture', type=int, default=0, help="run a capture (assumes ADC present)")    
    parser.add_argument('--nchan', type=int, default=32, help='channel count for pattern')
    parser.add_argument('--awglen', type=int, default=2048, help='samples in AWG waveform')
    parser.add_argument('--post', type=int, default=100000, help='samples in ADC waveform')
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('uuts', nargs=1, help="uut ")
    run_shots(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()



