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

import os
import sys
import matplotlib.pyplot as plt
from builtins import input
import hashlib

import time
from functools import wraps

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print('TIMING:func:%r took: %2.2f sec' % (f.__name__, te-ts))
        return result
    return wrap


def configure_sig_gen(args):
    sg = acq400_hapi.Agilent33210A(args.uuts[1])
    sg.config(1000)
    sg.config_free_running_burst(ncyc=2, rate=10)


def configure_ai(args, uut):
    uut.s0.transient = "PRE=%d POST=%d SOFT_TRIGGER=0 DEMUX=0" % (0, args.post)
#    for sx in uut.modules:
#        uut.modules[sx].trg = '1,0,1'


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


@timing
def run_oneshot(uut):
    uut.run_oneshot()

@timing
def read_xx(args, uut):
    return uut.read_chan(0, args.post * args.nchan)

def run_shots(args):
    file_num = 0
    cycle = 0
    root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
    make_data_dir(root, args.verbose)
    uut = acq400_hapi.Acq400(args.uuts[0])
    acq400_hapi.Acq400UI.exec_args(uut, args)
    #configure_ai(args, uut)
    if args.sg == 1:
        configure_sig_gen(args)

    if args.loop == -1:
        args.loop = sys.maxint
    lp = 0
    while lp < args.loop:
        if args.wait_user == 1:
            input("Hit any key to continue: ")

        run_oneshot(uut)

        if args.store == 1:
            if file_num > 99:
                file_num = 0
                cycle += 1
                root = args.root + args.uuts[0] + "/" + "{:06d}".format(cycle)
                make_data_dir(root, args.verbose)

            rdata = read_xx(args, uut)

            if args.plot == 1:
                plt.plot(rdata[0:-1:args.nchan]) # plots first channel
                plt.show()

            fn = "{}/{:04d}".format(root, file_num)
            if args.verbose:
                print("write {} bytes to file {} {}".format(len(rdata), fn, hashlib.sha1(rdata).hexdigest()))

            with open(fn, "wb+") as data_file:
                data_file.write(rdata)
            file_num += 1
            lp += 1


def run_main():
    parser = argparse.ArgumentParser(description='acq1001 HIL demo')
    acq400_hapi.Acq400UI.add_args(parser, transient=True, demux=0)
    parser.add_argument('--store', type=int, default=1, help='Whether to store data or not')
    # parser.add_argument('',type=int, default=1, help='')
    parser.add_argument('--sg',type=int, default=0, help='Whether to configure a sig gen. Default = False')
    parser.add_argument('--plot',type=int, default=0, help='Plot CH01 for monitoring purposes. Not intended for scope UI.')
    parser.add_argument('--wait_user', type=int, default=0, help='If wait_user is true then wait for user input between each shot.')
    parser.add_argument('--verbose', type=int, default=0, help="Verbosity")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--loop', type=int, default=1, help="loop count")
    parser.add_argument('--nchan', type=int, default=128, help='channel count for pattern')
    parser.add_argument('uuts', nargs="+", help="uut ")
    run_shots(parser.parse_args())

if __name__ == '__main__':
    run_main()
