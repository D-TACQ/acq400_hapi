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


def _load_awg(uut, fn, autorearm):
    with open(fn, "rb") as fd:
        uut.load_awg(fd.read(), autorearm=autorearm)

def load_awg(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    _load_awg(uut, args.file, args.mode==2)




def run_main():
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default="", help="file to load")
    parser.add_argument('--mode', default=2, type=int, help="mode: 1 oneshot, 2 oneshot_autorearm")
    parser.add_argument('uuts', nargs=1, help="uut ")
    load_awg(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
