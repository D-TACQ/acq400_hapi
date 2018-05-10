#!/usr/bin/env python
# Hardware In Loop : load AO data,run a shot, get AI data, repeat.
# upload to AWG and optionally run a capture.
# data for upload is either File (host-local data file) or Rainbow, a test pattern.
# assumes that clocking has been pre-assigned.

import sys
import acq400_hapi
import awg_data
import argparse

def store_file(it, rdata, nchan, nsam):
    fn = 'DATA/ai%04d.dat' % (it)
    print("store_file {}".format(fn))
    
    with open(fn, 'wb') as f:
        f.write(rdata)

def run_shots(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    acq400_hapi.cleanup.init()
    
    uut.s0.transient = 'POST=%d SOFT_TRIGGER=%d DEMUX=%d' % \
            (args.post, 1 if args.trg == 'int' else 0, 1 if args.store==0 else 0)    

    if args.aochan == 0:
        args.aochan = args.nchan

    for sx in uut.modules:
        uut.modules[sx].trg = '1,1,1'  if args.trg == 'int' else '1,0,1'

    if args.files != "":
        work = awg_data.RunsFiles(uut, args.files.split(','), True)
    else:
        work = awg_data.RainbowGen(uut, args.aochan, args.awglen, True)
        
    store = store_file
    loader = work.load()
    for ii in range(0, args.loop):
        print("shot: %d" % (ii))
        f = loader.next()
        print("Loaded %s" % (f))
        uut.run_oneshot()

        if args.store:
            print("read_chan %d" % (args.post*args.nchan))
            rdata = uut.read_chan(0, args.post*args.nchan)            
            store(ii, rdata, args.nchan, args.post)
        if args.wait_user:
            raw_input("hit return to continue")


def run_main():
    parser = argparse.ArgumentParser(description='acq1001 HIL demo')
    parser.add_argument('--files', default="", help="list of files to load")
    parser.add_argument('--loop', type=int, default=1, help="loop count") 
    parser.add_argument('--store', type=int, default=1, help="save data when true") 
    parser.add_argument('--nchan', type=int, default=32, help='channel count for pattern')
    parser.add_argument('--aochan', type=int, default=0, help='AO channel count, if different to AI (it happens)')
    parser.add_argument('--awglen', type=int, default=2048, help='samples in AWG waveform')
    parser.add_argument('--post', type=int, default=100000, help='samples in ADC waveform')
    parser.add_argument('--trg', default="int", help='trg "int|ext rising|falling"')
    parser.add_argument('--wait_user', type=int, default=0, help='1: force user input each shot')
    parser.add_argument('uuts', nargs=1, help="uut ")
    run_shots(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()

