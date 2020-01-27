#!/usr/bin/env python3

"""
A python script to start a stream and pull data from port 4210.
Once the data is pulled it is sorted by channel and saved to
files in channelised order.
"""


import acq400_hapi
import numpy as np
import matplotlib.pyplot as plt
import argparse
import socket
import os
import datetime
import time


def create_data_dir(args):
    """
    A function to create the new directory in which to store data.
    """

    try:
        os.makedirs(args.data_dir)
    except Exception:
        print("Tried to create dir but dir already exists")
        pass
    return None


def configure_uut(args, uut):
    """
    A function to configure the UUT for an RTM capture.
    """
    uut.s1.trg = '1,1,1'
    uut.s1.rgm = '3,0,0'

    # RTM_TRANSLEN should be adjusted to be 1 less than than the bufferlen as
    # we are relying on an event sample every trigger (every buffer).
    uut.s1.RTM_TRANSLEN = args.rtm_translen - 1
    uut.s0.bufferlen = args.rtm_translen * int(uut.nchan())
    return None


def start_stream(args, uut):
    data_file = None
    skt = socket.socket()
    skt.connect((args.uut[0], 4210))

    data_file = open("{}/{}".format(args.data_dir, "muxed_data.dat"), "wb")
    bytes_written = 0

    # while True is okay for now, as we don't know how long the capture should
    # actually be. Once the length is decided this should be adjusted.
    while True:

        data = skt.recv(4096*32*2)
        data_file.write(data)

        bytes_written += len(data)
        if bytes_written % 2**20 == 0:
            print("megabytes written: {}".format(bytes_written / 1024**2))


    return None


def main():
    parser = argparse.ArgumentParser(description='Streaming RTM')

    parser.add_argument('--rtm_translen', default=4096, type=int,
    help='How many samples to capture after each trigger.')

    parser.add_argument('--data_dir', default='default', type=str,
    help='Where to store your data. If left as default then data will be' \
    ' stored under [uut_name]_[datetime]')

    parser.add_argument('uut', nargs='+', help="Name of uut to stream.")
    args = parser.parse_args()

    uut = acq400_hapi.Acq400(args.uut[0])

    if args.data_dir == 'default':
        args.data_dir = './' + args.uut[0] + '_' + datetime.datetime.now().strftime("%y%m%d%H%M") + '/'
    print(args.data_dir)

    nchan = uut.nchan()

    configure_uut(args, uut)
    create_data_dir(args)
    start_stream(args, uut)

    return None


if __name__ == '__main__':
    main()
