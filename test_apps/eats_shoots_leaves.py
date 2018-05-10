#!/usr/bin/env python
# eats_shoots_leaves.py
# connect to PANDA service and output data

import sys
import acq400_hapi
import argparse


def run_command(args):
    skt = acq400_hapi.Netclient(args.uut[0], args.port)
    skt.sock.send(("{}\n".format(args.cmd)).encode())
    buffer = skt.sock.recv(args.rxlen)
    print(buffer)

def run_main():
    parser = argparse.ArgumentParser(description="connect to panda service, output data")
    parser.add_argument('--cmd', default="NO_STATUS NO_HEADER")
    parser.add_argument('--port', default="8889")
    parser.add_argument('--rxlen', default=4096)
    parser.add_argument('uut', nargs=1, help="uut name or ip")
    run_command(parser.parse_args())
# execution starts here

if __name__ == '__main__':
    run_main()

