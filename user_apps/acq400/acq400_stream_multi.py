#!/usr/bin/env python

"""
This is a script intended to connect to a UUT and stream data from port 4210.

The data that has been streamed is not demuxed and so if it is to be used then it has to be demuxed first.
Something like:

    >>> data = numpy.fromfile("0000", dtype="<datatype>")
    >>> plt.plot(data[::<number of channels>])
    >>> plt.show()

usage::
    acq400_stream.py [-h] [--filesize FILESIZE] [--totaldata TOTALDATA]
                        [--root ROOT] [--runtime RUNTIME] [--verbose VERBOSE]
                        uuts [uuts ...]

acq400 stream

positional arguments:
  uuts                  uuts

optional arguments:
  -h, --help            show this help message and exit
  --filesize FILESIZE   Size of file to store in KB. If filesize > total data
                        then no data will be stored.
  --totaldata TOTALDATA
                        Total amount of data to store in KB
  --root ROOT           Location to save files
  --runtime RUNTIME     How long to stream data for
  --verbose VERBOSE     Prints status messages as the stream is running


Some usage examples are included below:

1: Acquire files of size 1024kb up to a total of 4096kb:


    >>> python acq400_stream.py --verbose=1 --filesize=1M --totaldata=4M <module ip or name>

2: Acquire a single file of size 4096kb:


    >>> python acq400_stream.py --verbose=1 --filesize=4M --totaldata=4M <module ip or name>

3: Acquire files of size 1024 for 10 seconds:


    >>> python acq400_stream.py --verbose=1 --filesize=1M --runtime=10 <module ip or name>

4: Acquire data for 5 seconds and write the data all to a single file:


    >>> python acq400_stream.py --verbose=1 --filesize=9999M --runtime=5 <module ip or name>

"""

import acq400_hapi
import numpy as np
import os
import time
import argparse
import sys
import shutil

import multiprocessing
import threading

def make_data_dir(directory, verbose):
    if verbose > 2:
        print("make_data_dir {}".format(directory))
    try:
        os.makedirs(directory)
    except Exception:
        if verbose > 2:
            print("Directory already exists")
        pass

def remove_stale_data(args):
    for uut in args.uuts:
        path = os.path.join(args.root, uut)
        if os.path.exists(path):
            if args.force_delete:
                pass
            else:
                answer = input("Stale data detected. Delete all contents in " + args.root + str(args.uuts[0]) + "? y/n ")
                if answer != 'y':
                    continue
            if args.verbose:
                print("removing {}".format(path))
            shutil.rmtree(path)

def self_burst_trigger_callback(uut):
    def cb():
        uut.s0.soft_trigger = 1
    return cb

def self_start_trigger_callback(uut):
    def cb():
        print("self_start_trigger_callback")
        while uut.s0.state.split(' ')[0] != '1':
            time.sleep(0.5)
        uut.s0.soft_trigger = 1
    return cb

class StreamsOne:
    def __init__ (self, args, uut_name):
        self.args = args
        self.uut_name = uut_name

    def logtime(self, t0, t1):
        print(int((t1-t0)*1000), file=self.log_file)
        return t1


    def run(self, callback=None):
        uut = acq400_hapi.Acq400(self.uut_name)
        cycle = -1
        fnum = 999       # force initial directory create
        data_bytes = 0
        files = 0

        if callback is None:
            callback = lambda : False

        if self.args.burst_on_demand:
            uut.s1.rgm='3,1,1'
            uut.s1.RTM_TRANSLEN = self.args.burst_on_demand
            self.args.filesamples = self.args.burst_on_demand
            if self.args.trigger_from_here != 0:
                callback = self_burst_trigger_callback(uut)
                self.thread = threading.Thread(target=self_start_trigger_callback(uut))
                self.thread.start()

        try:
            if int(uut.s0.data32):
                data_size = 4
                wordsizetype = "<i4"  # 32 bit little endian
            else:
                wordsizetype = "<i2"  # 16 bit little endian
                data_size = 2
        except AttributeError:
            print("Attribute error detected. No data32 attribute - defaulting to 16 bit")
            wordsizetype = "<i2"  # 16 bit little endian
            data_size = 2

        netssb = int(uut.s0.ssb)
        if self.args.subset:
            c1,clen = [ int(x) for x in self.args.subset.split(',')]
            netssb = clen * data_size

        if self.args.filesamples:
            self.args.filesize = self.args.filesamples*netssb

        blen = self.args.filesize//data_size

        if self.args.burst_on_demand and self.args.verbose:
            print(f'burst_on_demand RTM_TRANSLEN={self.args.burst_on_demand} netssb={netssb} filesize={self.args.filesize} blen={blen}')

        self.log_file = open("{}_times.log".format(self.uut_name), "w")
        t_run = 0
        fn = "no-file"

        for buf in uut.stream(recvlen=blen, data_size=data_size):
            if data_bytes == 0:
                t0 = time.time()
            else:
                t_run = self.logtime(t0, time.time()) - t0

            data_bytes += len(buf) * data_size

            if len(buf) == 0:
                print("Zero length buffer, quit")
                return

            if not self.args.nowrite:
                if fnum >= self.args.files_per_cycle:
                    fnum = 0
                    cycle += 1
                    root = os.path.join(self.args.root, self.uut_name, "{:06d}".format(cycle))
                    make_data_dir(root, self.args.verbose)

                fn = os.path.join(root, "{:04d}.dat".format(fnum))
                data_file = open(fn, "wb")
                buf.tofile(data_file, '')
                files += 1
                if self.args.verbose > 3:
                    print(f'wrote file: {fn}')

            if self.args.verbose == 0:
                pass
            elif self.args.verbose == 1:
                print(".", end='')
            elif t_run > 0 and (self.args.verbose > 2 or fnum == 0):
                print("{:8.3f} {} files {:4d} total bytes: {:10d} rate: {:.2f} MB/s".
                          format(t_run, fn, files, int(data_bytes), data_bytes/t_run/0x100000))
            fnum += 1

            if callback() or t_run >= self.args.runtime or data_bytes > self.args.totaldata:
                break
        
        uut.stream_close()
                


def status_cb():
    print("Another one")
    
def run_stream_run(args):
    RXBUF_LEN = 4096
    cycle = 1
    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
    data = bytes()
    num = 0

    args.ps = []

    # run all slave units su in separate processes
    for su in reversed(args.uuts[1:]):
        streamer = StreamsOne(args, su)
        ps = multiprocessing.Process(target=streamer.run, name=su, daemon=True)
        args.ps.append(ps)
        ps.start()

    # run master in foreground process.
    ms = StreamsOne(args, args.uuts[0])
    if len(args.uuts) > 1:
        print("Pausing 2 before launching M")
        time.sleep(2)

    ms.run(callback=args.callback)
#    ms.run(callback=status_cb)

def run_stream_prep(args):
    if args.filesize > args.totaldata:
            args.filesize = args.totaldata
    remove_stale_data(args)
    return args

def tidy_up(args):
    for ps in args.ps:
        if ps.exitcode is None:
            ps.terminate()
            ps.join()

def get_parser(parser=None):
    if not parser:
        is_client = True        
        parser = argparse.ArgumentParser(description='acq400 stream')
        parser.add_argument('--callback', default=None, help='not for users, client programs can install a callback here')
    else:
        is_client = False
        
    #parser.add_argument('--filesize', default=1048576, type=int,
    #                    help="Size of file to store in KB. If filesize > total data then no data will be stored.")
    parser.add_argument('--burst_on_demand', default=None, action=acq400_hapi.intSIAction, decimal=False, help="Burst Size in Samples [binary M]")
    parser.add_argument('--trigger_from_here', default=0, type=int, help="action soft trigger from this application")
    parser.add_argument('--subset', default=None, help='subset command if present eg 1,5 :: strips first 5 channels')
    parser.add_argument('--filesize', default=0x100000, action=acq400_hapi.intSIAction, decimal=False, help="file size in bytes")
    parser.add_argument('--filesamples', default=None, action=acq400_hapi.intSIAction, decimal=False, help="file size in samples (overrides filesize)")
    parser.add_argument('--files_per_cycle', default=100, type=int, help="files per cycle (directory)")
    parser.add_argument('--force_delete', default=0, type=int, help="silently delete any existing data files")
    parser.add_argument('--nowrite', default=0, help="do not write file")
    parser.add_argument('--totaldata', default=10000000000, action=acq400_hapi.intSIAction, decimal = False)
    #parser.add_argument('--totaldata', default=4194304, type=int, help="Total amount of data to store in KB")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    if is_client:
        parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

def run_stream(args):
    run_stream_prep(args)
    run_stream_run(args)
    tidy_up(args)

def run_main():
    run_stream(get_parser().parse_args())


if __name__ == '__main__':
    run_main()
