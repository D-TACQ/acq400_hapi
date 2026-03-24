#!/usr/bin/env python3

"""
Read the loaded STL

Usage:

    ./user_apps/acq400/acq400_read_stl.py acq1102_010
"""

import acq400_hapi
import argparse
import socket

def run_main(args):    
    uut = acq400_hapi.factory(args.uutname)
    stl = uut.read_stl()
    print(''.join(stl))

def get_parser():
    parser = argparse.ArgumentParser(description='Read the loaded STL')

    parser.add_argument('uutname', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())