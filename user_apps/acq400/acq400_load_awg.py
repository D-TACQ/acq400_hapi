#!/usr/bin/env python

"""
upload file to AWG for a one-shot play
data for upload is a single file
assumes that clocking has been pre-assigned.


positional arguments:
  uuts               uut

optional arguments:
  -h, --help         show this help message and exit
  --files FILES      list of files to load
"""

import sys
import socket

import acq400_hapi
from acq400_hapi import awg_data
from acq400_hapi import netclient as netclient
import argparse


def _load_awg(uut, fn, port):
    eof = False
    bn = 0
    with open(fn, "rb") as fd:
        with netclient.Netclient(uut.uut, port) as nc:
            while not eof:
                chunk = fd.read(0x100000)
                if len(chunk) == 0:
                    eof = True
                else:
                    nc.sock.send(chunk)
                    sys.stderr.write('\r{}'.format(bn))
                    bn += 1
            nc.sock.shutdown(socket.SHUT_WR)
            sys.stderr.write('\nsocket SHUT_WR, wait for DONE\n')
            while True:
                rx = nc.sock.recv(128)
                if not rx or rx.startswith(b"DONE"):
                    break
            nc.sock.close()
            sys.stderr.write("DONE\n")
        
def load_awg(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    _load_awg(uut, args.file, 54201)


            

def run_main():
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default="", help="file to load")
    parser.add_argument('uuts', nargs=1, help="uut ")
    load_awg(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()



