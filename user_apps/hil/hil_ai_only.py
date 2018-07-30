"""
hil_ai_only.py is a script that configures a signal generator along with a
UUT to take repeated transient captures. This is similar to a hardware in the loop
test, only with the AO module replaced by the sig gen.

Data is saved (muxed) to disk.

Example usage:

Capture for 4 loops:
    >>> python hil_ai_only.py --loop=4 --verbose=1 --wait_user=1 acq1001_339 10.12.196.155

Capture for infinty:
    >>> python hil_ai_only.py --loop=-1 --verbose=1 acq1001_339 10.12.196.155
"""


import argparse
import acq400_hapi
import socket
import os
import sys
from builtins import input


def configure_sig_gen(args):
    skt = socket.socket()
    skt.connect((args.uuts[1], 5025))
    skt.send(b"SYST:BEEP")
    skt.send(b"OUTP OFF")
    skt.send(b"TRIG:SOUR IMM")
    skt.send(b"BURS:INT:PER 10")
    skt.send(b"BURS:NCYC {}".format(args.loop))
    skt.send(b"BURS:MODE TRIG")
    skt.send(b"OUTP ON")


def configure_ai(args, uut):
    for sx in uut.modules:
        uut.modules[sx].trg = '1,0,1'


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


def run_shots(args):
    file_num = 0
    cycle = 0
    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
    make_data_dir(root, args.verbose)
    uut = acq400_hapi.Acq400(args.uuts[0])
    uut.s0.transient = "PRE=%d POST=%d SOFT_TRIGGER=0" % (0, 100000)
    uut.s0.set_arm = 1

    configure_ai(args, uut)
    configure_sig_gen(args)
    skt = socket.socket()
    skt.connect((args.uuts[0], 2235))

    if args.loop == -1:
        args.loop = sys.maxint
    lp = 0
    #for lp in range(0, args.loop):
    while lp < args.loop:
        if args.wait_user == 1:
            input("Hit any key to continue: ")
        uut.s0.set_arm = 1
        while True:
            trn_stat = str(skt.recv(4096))
            if "0 0 " + str(args.post) in trn_stat:
                break

        if args.store == 1:
            if file_num > 99:
                file_num = 0
                cycle += 1
                root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)

            rdata = uut.read_chan(0, args.post * args.nchan)
            data_file = open("{}/{:04d}".format(root, file_num), "wb+")
            data_file.write(rdata)
            file_num += 1
            lp += 1


def run_main():
    parser = argparse.ArgumentParser(description='acq1001 HIL demo')
    parser.add_argument('--store', type=int, default=1, help='Whether to store data or not')
    # parser.add_argument('',type=int, default=1, help='')
    parser.add_argument('--wait_user', type=int, default=0, help='If wait_user is true then wait for user input between each shot.')
    parser.add_argument('--verbose', type=int, default=0, help="Verbosity")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--loop', type=int, default=1, help="loop count")
    parser.add_argument('--nchan', type=int, default=32, help='channel count for pattern')
    parser.add_argument('--post', type=int, default=100000, help='samples in ADC waveform')
    parser.add_argument('uuts', nargs=2, help="uut ")
    run_shots(parser.parse_args())

if __name__ == '__main__':
    run_main()
