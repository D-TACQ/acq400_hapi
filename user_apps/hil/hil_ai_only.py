"""
hil_ai_only.py is a script that configures a signal generator along with a
UUT to take repeated transient captures. This is similar to a hardware in the loop
test, only with the AO module replaced by the sig gen.

Data is saved (muxed) to disk.

Example usage:

Capture for 4 loops:
    >>> python hil_ai_only.py --loop=4 --verbose=1 --wait_user=1 <UUT name>

Capture for infinty:
    >>> python hil_ai_only.py --loop=-1 --verbose=1 <UUT name>
"""


import argparse
import acq400_hapi
import socket
import os
import sys
import matplotlib.pyplot as plt
from builtins import input


def configure_sig_gen(args):
    skt = socket.socket()
    skt.connect((args.uuts[1], 5025))
    skt.send(b"SYST:BEEP")
    skt.send(b"OUTP OFF")
    skt.send(b"TRIG:SOUR IMM")
    skt.send(b"BURS:INT:PER 10")
    skt.send(b"BURS:NCYC 2")
    skt.send(b"BURS:MODE TRIG")
    skt.send(b"OUTP ON")


def configure_ai(args, uut):
    uut.s0.transient = "PRE=%d POST=%d SOFT_TRIGGER=0 DEMUX=0" % (0, args.post)
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
    acq400_hapi.Acq400UI.exec_args(uut, args)
    configure_ai(args, uut)
    if args.sg == 1:
        configure_sig_gen(args)

    if args.loop == -1:
        args.loop = sys.maxint
    lp = 0
    while lp < args.loop:
        if args.wait_user == 1:
            input("Hit any key to continue: ")

        uut.run_oneshot()

        if args.store == 1:
            if file_num > 99:
                file_num = 0
                cycle += 1
                root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
                make_data_dir(root, args.verbose)

            rdata = uut.read_chan(0, args.post * args.nchan)

            if args.plot == 1:
                plt.plot(rdata[0:-1:args.nchan]) # plots first channel
                plt.show()

            data_file = open("{}/{:04d}".format(root, file_num), "wb+")
            data_file.write(rdata)
            file_num += 1
            lp += 1


def run_main():
    parser = argparse.ArgumentParser(description='acq1001 HIL demo')
    acq400_hapi.Acq400UI.add_args(parser, post=False, pre=True)
    parser.add_argument('--store', type=int, default=1, help='Whether to store data or not')
    # parser.add_argument('',type=int, default=1, help='')
    parser.add_argument('--sg',type=int, default=0, help='Whether to configure a sig gen. Default = False')
    parser.add_argument('--plot',type=int, default=0, help='Plot CH01 for monitoring purposes. Not intended for scope UI.')
    parser.add_argument('--wait_user', type=int, default=0, help='If wait_user is true then wait for user input between each shot.')
    parser.add_argument('--verbose', type=int, default=0, help="Verbosity")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--loop', type=int, default=1, help="loop count")
    parser.add_argument('--nchan', type=int, default=128, help='channel count for pattern')
    parser.add_argument('--post', type=int, default=100000, help='samples in ADC waveform')
    parser.add_argument('uuts', nargs="+", help="uut ")
    run_shots(parser.parse_args())

if __name__ == '__main__':
    run_main()
