#!/usr/bin/env python

"""
This is a script intended to connect to a UUT and stream data from port 4210.

The data that has been streamed is not demuxed and so if it is to be used then it has to be demuxed first.
Something like:

    >>> data = numpy.fromfile("data0.dat", dtype="<datatype>")
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


    >>> python acq400_stream.py --verbose 1 --filesize 1024 --totaldata 4096 --runtime 1000 <module ip or name>

2: Acquire a single file of size 4096kb:


    >>> python acq400_stream.py --verbose 1 --filesize 4096 --totaldata 4096 --runtime 1000 <module ip or name>

3: Acquire files of size 1024 for 10 seconds:


    >>> python acq400_stream.py --verbose 1 --filesize 1024 --totaldata 999999 --runtime 10 <module ip or name>

4: Acquire data for 5 seconds and write the data all to a single file:


    >>> python acq400_stream.py --verbose 1 --filesize 999999 --totaldata 999999 --runtime 5 <module ip or name>

"""

import acq400_hapi
import numpy as np
import os
import time
import argparse


def make_data_dir(directory, verbose):
    try:
        os.mkdir(directory)
    except Exception:
        if verbose:
            print "Directory already exists"
        pass


def run_stream(args):
    data = ""
    num = 0
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for uut in uuts:
        try:
            if uut.s0.data32:
                wordsizetype = "<i4"  # 32 bit little endian
        except AttributeError:
            print("Attribute error detected. No data32 attribute - defaulting to 16 bit")
            wordsizetype = "<i2"  # 16 bit little endian

        skt = acq400_hapi.Netclient(args.uuts[0], 4210)
        make_data_dir(args.root, args.verbose)
        start_time = time.clock()
        upload_time = time.clock()
        data_length = 0

        while time.clock() < (start_time + args.runtime) and data_length < args.totaldata:

            loop_time = time.clock()
            data += skt.sock.recv(10240000)

            if len(data) / 1024 >= args.filesize:
                data_length += float(len(data)) / 1024
                data_file = open("{}/data{}.dat".format(args.root, num), "wb")
                data = np.frombuffer(data, dtype=wordsizetype, count=-1)
                data.tofile(data_file, '')

                if args.verbose == 1:
                    print "New data file written."
                    print "Data Transferred: ", data_length, "KB"
                    print "loop_time: ", loop_time
                    print "Data upload & save rate: ", float(len(data)) / 1024 / (time.clock() - upload_time), "KB/s"
                    print ""
                    print ""

                num += 1
                data_file.close()
                data = ""  # Remove data from variable once it has been written
                upload_time = time.clock()  # Reset upload time
                data_written_flag = 1

        try:
            data_written_flag
        except NameError:
            data_file = open("{}/data{}.dat".format(args.root, num), "wb")
            data = np.frombuffer(data, dtype=wordsizetype, count=-1)
            data.tofile(data_file, '')
            print "runtime exceeded: all stream data written to single file"


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    parser.add_argument('--filesize', default=1024, type=int,
                        help="Size of file to store in KB. If filesize > total data then no data will be stored.")
    parser.add_argument('--totaldata', default=4096, type=int, help="Total amount of data to store in KB")
    parser.add_argument('--root', default="ROOT", type=str, help="Location to save files")
    parser.add_argument('--runtime', default=1000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('uuts', nargs='+', help="uuts")
    run_stream(parser.parse_args())


if __name__ == '__main__':
    run_main()
