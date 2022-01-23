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
import re

HYSTAT = 61002

def make_data_dir(directory, verbose):
    if verbose:
        print("make_data_dir {}".format(directory))
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Directory already exists")
        pass

def remove_stale_data(args, path):
    if os.path.exists(path):
        if args.force_delete:
            pass
        else:
            answer = input("Stale data detected. Delete all contents in " + args.root + uut + "? y/n ")
            if answer != 'y':
                return
        if args.verbose:
            print("removing {}".format(path))          
        shutil.rmtree(path)
            
class StreamsOne:
    def __init__ (self, args, uut_name):
        self.args = args
        self.uut_name = uut_name
        self.uut = acq400_hapi.Acq400(self.uut_name)
        self.root = os.path.join(self.args.root, self.uut_name)
        remove_stale_data(args, self.root) 
        make_data_dir(self.root, self.args.verbose)
        self.filename = "nothing"
        self.newname = "default" 
        self.data_file = None       
        
        self.filename_source = acq400_hapi.Netclient(self.uut.uut, HYSTAT)
        self.filename_source.termex = re.compile(r"(HY\-stat>)")
        self.filename_re = re.compile(r"(NEW|OLD) (\w+)")
        self.filename_source.send("\r\n")        


    def logtime(self, t0, t1):
        print(int((t1-t0)*1000), file=self.log_file)
        return t1

    def open_data_file(self):
        if self.filename_source.has_data():
            message = self.filename_source.receive_message(self.filename_source.termex)
            m = self.filename_re.search(message)
            if not m:
                print("ERROR match failed {}".format(message))
                sys.exit()
            self.newname = m.group(2)
            if self.newname == "QUIT":
                print("Quitting on remote request")
                sys.exit(0)
                 
        if self.filename != self.newname:
            fullpath = os.path.join(self.root, self.newname)
            self.data_file = open(fullpath, "wb")
            self.filename = self.newname
            if self.args.verbose > 1:
                print("open_data_file() {}".format(fullpath))

    def run(self):        
        data_length = 0
        self.open_data_file()    # might be QUIT
        if self.args.burstlen > self.args.totaldata:
            self.args.burstlen = self.args.totaldata
        try:
            if int(self.uut.s0.data32):
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
            
        for buf in self.uut.stream(recvlen=self.args.burstlen, data_size=data_size):
            if data_length > 0:
                t0 = self.logtime(t0, time.time())
            else:
                t0 = time.time()

            data_length += len(buf)
            
            if len(buf) == 0:
                print("Zero length buffer, quit")
                return

            if not self.args.nowrite: 
                if not self.data_file:
                    self.open_data_file()
                buf.tofile(self.data_file, '')
                
                if self.args.verbose == 1:
                    print(".", end='')
                    
                # maybe the filename must change?. Now is a good time                    
                self.open_data_file()
                
            if time.time() >= (start_time + self.args.runtime) or data_length > self.args.totaldata:                
                return
            

def run_stream(args):
    streamer = StreamsOne(args, args.uut[0])
    streamer.run()

def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    #parser.add_argument('--burstlen', default=1048576, type=int,
    #                    help="Size of file to store in KB. If burstlen > total data then no data will be stored.")
    parser.add_argument('--burstlen', default=0x100000, action=acq400_hapi.intSIAction, decimal=False, help="burst length in samples")    
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
