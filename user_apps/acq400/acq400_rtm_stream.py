#!/usr/bin/env python3

"""A python script to start a stream and pull data from port 4210.

Once the data is pulled it is sorted by channel and saved to
files in channelised order.
"""


import acq400_hapi
import argparse
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

class FileSink:
    def __init__(self, args):
        self.data_file = open("{}/{}".format(args.data_dir, "muxed_data.dat"), "wb")
        self.bytes_written = 0
        
    def __call__(self, data):
        self.data_file.write(data)

        self.bytes_written += len(data)
        if self.bytes_written % 2**12 == 0:
            print("pages written: {}".format(self.bytes_written / 1024**2))
        return False
    
def FileSinkFun(args):
    data_file = open("{}/{}".format(args.data_dir, "muxed_data.dat"), "wb")
    bytes_written = 0
    
    def sink(data):
        nonlocal bytes_written
        data_file.write(data)

        bytes_written += len(data)
        if bytes_written % 2**12 == 0:
            print("pages written: {}".format(bytes_written / 1024**2))
        return False
    
    return sink
    

def main(args):
    uut = acq400_hapi.factory(args.uut[0])

    if args.data_dir == 'default':
        args.data_dir = './' + args.uut[0] + '_' + datetime.datetime.now().strftime("%y%m%d%H%M") + '/'
    print(args.data_dir)

    nchan = uut.nchan()

    #configure_uut(args, uut)
    create_data_dir(args)
    #uut.stream(FileSink(args))
    uut.stream(FileSinkFun(args))

    return None

def get_parser():
    parser = argparse.ArgumentParser(description='Start RTM stream')
    parser.add_argument('--rtm_translen', default=4096, type=int,
    help='How many samples to capture after each trigger.')

    parser.add_argument('--data_dir', default='default', type=str,
    help='Where to store your data. If left as default then data will be' \
    ' stored under [uut_name]_[datetime]')

    parser.add_argument('uut', nargs='+', help="Name of uut to stream.")
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())