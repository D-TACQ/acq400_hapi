
import acq400_hapi
import numpy as np
import os
import time
import argparse
import socket
import sys
import shutil

def remove_stale_data(args):
    if os.path.exists(args.uuts[0]):
        answer = raw_input("Stale data detected. Delete all contents in " + str(args.uuts[0]) + "? y/n ")
        if answer == "y":
            shutil.rmtree(args.uuts[0])
        else:
            pass


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Directory already exists")
        pass


def run_stream(args):
    remove_stale_data(args)
    data_len_so_far = 0
    RXBUF_LEN = 4096
    cycle = 1
    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
    data = bytes()
    file_num = 0
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

        while time.time() < (start_time + args.runtime) and data_len_so_far < args.totaldata:
            bytestogo = args.filesize - data_length
            rxbuf_len = RXBUF_LEN if bytestogo > RXBUF_LEN else bytestogo
            loop_time = time.clock()
            data = skt.recv(rxbuf_len)

            data_length += len(data)
            data_len_so_far += len(data)
            if file_num > 99:
                file_num = 0
                cycle += 1
                root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
                make_data_dir(root, args.verbose)

            data_file = open("{}/{:04d}".format(root, file_num), "ab")
            data_file.write(data)

            if data_length >= args.filesize:
                file_num += 1
                bytestogo = args.filesize
                data_length = 0
            data_file.close()
            upload_time = time.time()  # Reset upload time


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
