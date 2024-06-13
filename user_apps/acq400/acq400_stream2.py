#!/usr/bin/env python3

"""
This is a script intended to connect to a UUT and stream data from port 4210.

The data that has been streamed is not demuxed and so if it is to be used then it has to be demuxed first.
Something like:

    >>> data = numpy.fromfile("0000", dtype="<datatype>")
    >>> plt.plot(data[::<number of channels>])
    >>> plt.show()

Some usage examples are included below:

1: Acquire files of size 1024kb up to a total of 4096kb:


    >>> python acq400_stream2.py --verbose=1 --filesize=1M --totaldata=4M <module ip or name>

2: Acquire a single file of size 4096kb:


    >>> python acq400_stream2.py --verbose=1 --filesize=4M --totaldata=4M <module ip or name>

3: Acquire files of size 1024 for 10 seconds:


    >>> python acq400_stream2.py --verbose=1 --filesize=1M --runtime=10 <module ip or name>

4: Acquire data for 5 seconds and write the data all to a single file:


    >>> python acq400_stream2.py --verbose=1 --filesize=9999M --runtime=5 <module ip or name>

.. rst-class:: hidden

    usage::
        acq400_stream.py [-h] [--filesize FILESIZE] [--totaldata TOTALDATA]
                            [--root ROOT] [--runtime RUNTIME] [--verbose VERBOSE]
                            uuts [uuts ...]

    acq400 stream

    positional arguments:
    uuts                  uuts

    optional arguments:
    -h, --help            show this help message and exit
    --filesize FILESIZE   Size of file to store in KB. If filesize > total data\
        then no data will be stored.
    --totaldata TOTALDATA  Total amount of data to store in KB
    --root ROOT           Location to save files
    --runtime RUNTIME     How long to stream data for
    --verbose VERBOSE     Prints status messages as the stream is running


"""


import acq400_hapi
import numpy as np
import os
import time
import argparse
import socket
import sys
import shutil
from builtins import input


def remove_stale_data(args):
    if os.path.exists(args.root + args.uuts[0]):
        answer = input("Stale data detected. Delete all contents in " + args.root + str(args.uuts[0]) + "? y/n ")
        if answer == "y":
            shutil.rmtree(args.root + args.uuts[0])
        else:
            pass


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


def run_stream(args):
    remove_stale_data(args)
    uut = acq400_hapi.Acq400(args.uuts[0], monitor=False)
    data_len_so_far = 0
    RXBUF_LEN = 4096
    cycle = 1
    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
    file_num = 0

    if args.port == "STREAM":
        port = acq400_hapi.AcqPorts.STREAM
    elif args.port == "SPY":
        port = acq400_hapi.AcqPorts.DATA_SPY
        uut.s0.CONTINUOUS = "0"
        uut.s0.CONTINUOUS = "1"
    else:
        port = int(args.port)

    skt = socket.socket()
    skt.connect((args.uuts[0], port))
    make_data_dir(root, args.verbose)
    start_time = time.time()
    data_length = 0

    if args.es_stream:
        nchan = uut.s0.NCHAN
        ssb = uut.s0.ssb
        RXBUF_LEN = int(ssb)

    if args.filesize > args.totaldata:
        args.filesize = args.totaldata

    data_file = None
    current_fname = None
    time_left0 = 0

    while time.time() < (start_time + args.runtime) and data_len_so_far < args.totaldata:

        bytestogo = args.filesize - data_length

        if args.es_stream == 1 or bytestogo > RXBUF_LEN:
            rxbuf_len = RXBUF_LEN
        else:
            rxbuf_len = bytestogo

        data = skt.recv(rxbuf_len)

        data_length += len(data)
        data_len_so_far += len(data)
        if file_num >= args.files_per_cycle:
            file_num = 0
            cycle += 1
            root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
            make_data_dir(root, args.verbose)
        if data_file == None:
            current_fname = f'{root}/{file_num:04d}'
            data_file = open(current_fname, "wb")
        data_file.write(data)

        if args.verbose:
            time_left = -1 * (time.time() - (start_time + args.runtime))
            if time_left0 == 0:
                time_left0 = time_left
            elif time_left0 - time_left > 0.5:
                time_left0 = time_left

            if args.verbose > 1:
                print(f'Data {data_len_so_far} KB, time remaining {time_left:.2f} s')

        if args.es_stream == 1:
            if np.frombuffer(data, dtype=np.uint32)[2] == np.uint32(0xaa55f152):
                new_file_flag = True
                print("True")
            else:
                new_file_flag = False
        else:
            new_file_flag = True if data_length >= args.filesize else False

        if new_file_flag:
            file_num += 1
            data_length = 0
            data_file.close()
            data_file = None
            new_file_flag = False
            if args.verbose:
                file_mb = os.path.getsize(current_fname)//0x100000
                total_gb = data_len_so_far/0x40000000
                print(f'{current_fname} len {file_mb} MB total {total_gb:.1f} GB')

    if args.verbose:
        print()

    if args.verbose >= 1 and current_fname is not None:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(current_fname)
        print(f'File {current_fname} length {size} mtime {time.ctime(mtime)}')


def get_parser():
    parser = argparse.ArgumentParser(description='Stream data from UUT')
    parser.add_argument('-filesize', '--filesize', default=0x100000, action=acq400_hapi.intSIAction, decimal=False)
    parser.add_argument('--files_per_cycle', type=int, default=100, help="set files per cycle directory")
    parser.add_argument('-totaldata', '--totaldata', default=sys.maxsize, action=acq400_hapi.intSIAction, decimal = False)
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=sys.maxsize, type=int, help="How long to stream data for")
    parser.add_argument('--es_stream', default=0, type=int, help="Stream with ES. New file is used for each ES.")
    parser.add_argument('--port', default='STREAM', type=str, help="Which port to stream from. STREAM=4210, SPY=53667, other: use number provided.")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    run_stream(get_parser().parse_args())
