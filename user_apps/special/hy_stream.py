#!/usr/bin/env python

"""
hy_stream: stream data to file from port 4210. Get new file names from 61002  


"""

import acq400_hapi
import numpy as np
import os
import time
import argparse
import socket
import sys
import shutil

def make_data_dir(directory, verbose):
    if verbose:
        print("make_data_dir {}".format(directory))
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Directory already exists")
        pass

class StreamsOne:
    def __init__ (self, args, uut_name):
        self.args = args
        self.uut_name = uut_name

    def logtime(self, t0, t1):
        print(int((t1-t0)*1000), file=self.log_file)
        return t1


    def run(self):        
        uut = acq400_hapi.Acq400(self.uut_name)
        cycle = -1
        num = 999       # force initial directory create
        data_length = 0
        if self.args.filesize > self.args.totaldata:
            self.args.filesize = self.args.totaldata
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
            
        start_time = time.time()
        self.log_file = open("{}_times.log".format(self.uut_name), "w")
            
        for buf in uut.stream(recvlen=self.args.filesize, data_size=data_size):
            if data_length > 0:
                t0 = self.logtime(t0, time.time())
            else:
                t0 = time.time()

            data_length += len(buf)
            
            if len(buf) == 0:
                print("Zero length buffer, quit")
                return

            if not self.args.nowrite:
                if num >= self.args.files_per_cycle:
                    num = 0
                    cycle += 1
                    root = os.path.join(self.args.root, self.uut_name, "{:06d}".format(cycle))
                    make_data_dir(root, self.args.verbose)

                data_file = open(os.path.join(root, "{:04d}.dat".format(num)), "wb")
                buf.tofile(data_file, '')
                
                if self.args.verbose == 1:
                    print(".", end='')

                if self.args.verbose > 2:
                    print("New data file written.")
                    print("Data Transferred: ", data_length, "KB")
                    print("Streaming time remaining: ", -1*(time.time() - (start_time + self.args.runtime)))
                    print("")
                    print("")

            num += 1
                
            if time.time() >= (start_time + self.args.runtime) or data_length > self.args.totaldata:                
                return
            
               
    
def run_stream(args):
    RXBUF_LEN = 4096
    cycle = 1
    root = args.root + args.uut[0] + "/" + "{:06d}".format(cycle)
    data = bytes()
    num = 0
        
    streamer = StreamsOne(args, args.uut[0])
    streamer.run()

def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    #parser.add_argument('--filesize', default=1048576, type=int,
    #                    help="Size of file to store in KB. If filesize > total data then no data will be stored.")
    parser.add_argument('--filesize', default=0x100000, action=acq400_hapi.intSIAction, decimal=False)
    parser.add_argument('--files_per_cycle', default=100, type=int, help="files per cycle (directory)")
    parser.add_argument('--force_delete', default=0, type=int, help="silently delete any existing data files")
    parser.add_argument('--nowrite', default=0, help="do not write file")
    parser.add_argument('--totaldata', default=10000000000, action=acq400_hapi.intSIAction, decimal = False)
    #parser.add_argument('--totaldata', default=4194304, type=int, help="Total amount of data to store in KB")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('uut', nargs=1, help="uut")
    args = parser.parse_args()    
    run_stream(args)


if __name__ == '__main__':
    run_main()
