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
import socket
import sys

def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Directory already exists")
        pass


def run_stream(args):
    RXBUF_LEN = 4096
    cycle = 1
    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
    data = bytes()
    num = 0
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for uut in uuts:
        try:
            if int(uut.s0.data32):
                wordsizetype = "<i4"  # 32 bit little endian
            else:
                wordsizetype = "<i2"  # 16 bit little endian
        except AttributeError:
            print("Attribute error detected. No data32 attribute - defaulting to 16 bit")
            wordsizetype = "<i2"  # 16 bit little endian

        skt = socket.socket()
        skt.connect((args.uuts[0], 4210))
        make_data_dir(root, args.verbose)
        start_time = time.time()
        upload_time = time.time()
        data_length = 0
        if args.filesize > args.totaldata:
            args.filesize = args.totaldata
        bytestogo = args.filesize

        while time.time() < (start_time + args.runtime) and data_length < args.totaldata:
            rxbuf = RXBUF_LEN if bytestogo > RXBUF_LEN else bytestogo
            loop_time = time.clock()
            data += skt.recv(rxbuf)
            bytestogo = args.filesize - len(data)

            if len(data) >= args.filesize:
                data_length += len(data)
                if num > 99:
                    num = 0
                    cycle += 1
                    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
                    make_data_dir(root, args.verbose)

                data_file = open("{}/{:04d}".format(root, num), "wb")
                data = np.frombuffer(data, dtype="<i2")
                data = np.asarray(data)
                data.tofile(data_file, '')

                if args.verbose == 1:
                    print("New data file written.")
                    print("Data Transferred: ", data_length, "KB")
                    print("Streaming time remaining: ", -1*(time.time() - (start_time + args.runtime)))
                    print("")
                    print("")

                num += 1
                data_file.close()
                data = bytes()  # Remove data from variable once it has been written
                upload_time = time.time()  # Reset upload time
                data_written_flag = 1

        try:
            data_written_flag
        except NameError:
            data_file = open("{}/{:04d}".format(root, num), "wb")
            data = np.frombuffer(data, dtype="<i2")
            data = np.asarray(data)
            data.tofile(data_file, '')
            print("runtime exceeded: all stream data written to single file")


def run_main():
    parser = argparse.ArgumentParser(description='acq400 stream')
    #parser.add_argument('--filesize', default=1048576, type=int,
    #                    help="Size of file to store in KB. If filesize > total data then no data will be stored.")
    parser.add_argument('-filesize', '--filesize', default=0x100000, action=acq400_hapi.intSIAction, decimal=False)
    parser.add_argument('-totaldata', '--totaldata', default=sys.maxint, action=acq400_hapi.intSIAction, decimal = False)
    #parser.add_argument('--totaldata', default=4194304, type=int, help="Total amount of data to store in KB")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('uuts', nargs='+', help="uuts")

    run_stream(parser.parse_args())


if __name__ == '__main__':
    run_main()
