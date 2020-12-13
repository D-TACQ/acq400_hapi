#!/usr/bin/env python
""" mgtdramshot.py Capture to MGTDRAM

- optional capture to mgtdram
- manage upload
- optional validation
 assumes that clocking has been pre-assigned.

example usage::

       ./mgtdramshot.py --loop=100 --simulate=1 --validate=validate-6x480 \
           --captureblocks=2000 --offloadblocks=0-1999 acq2106_007


usage::

    mgtdramshot.py [-h] [--pre PRE] [--post POST] [--clk CLK] [--trg TRG]
                      [--sim SIM] [--trace TRACE] [--loop LOOP]
                      [--captureblocks CAPTUREBLOCKS]
                      [--offloadblocks OFFLOADBLOCKS] [--validate VALIDATE]
                      [--wait_user WAIT_USER]
                      uut

acq2106 mgtdram test

positional arguments:
  uut                   uut

optional arguments:
  -h, --help            show this help message and exit
  --pre PRE             pre-trigger samples
  --post POST           post-trigger samples
  --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG             int|ext,rising|falling
  --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE         1 : enable command tracing
  --loop LOOP           loop count
  --captureblocks CAPTUREBLOCKS
                        number of 4MB blocks to capture
  --offloadblocks OFFLOADBLOCKS
                        block list to upload nnn-nnn
  --validate VALIDATE   program to validate data
  --wait_user WAIT_USER
                        1: force user input each shot

"""

import sys
import datetime
import acq400_hapi
import argparse
from subprocess import call
import re
if sys.version_info < (3, 0):
    from future import builtins
    from builtins import input
import socket
import os
import numpy as np
try:
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except:
    HAS_PLOT = False
import time

LOG = None

MGT_BLOCK_BYTES = acq400_hapi.Acq2106_Mgtdram8.MGT_BLOCK_BYTES

def logprint(message):
    """
    logprint = 1: Print output only to stdout
    logprint = 2: Print output to stdout, also save to config file.
    """
    if _logprint:
        print(message)
    if _logprint > 1:
        with open("./mgt_{}.log".format(uut_name)) as fp:
            fp.write(message)
    return None


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


def validate_streamed_data(good_data, test_data, cycle):
    # Using this method there is no detectable overhead.

    compare_data = good_data + ((cycle) * good_data[-1])

    if not np.array_equal(test_data, compare_data[0:test_data.size]):
        print("Discrepency in data found in cycle: {}, quitting now.".format(cycle))
        print("Length good: {}, length test: {}".format(
            good_data.shape, test_data.shape))
        if HAS_PLOT:
            f, (ax1, ax2, ax3) = plt.subplots(3, 1, sharey=True)
            ax1.plot(compare_data)
            ax1.plot(test_data)
            ax2.plot(compare_data)
            ax3.plot(test_data)
            ax1.grid(True)
            ax2.grid(True)
            ax3.grid(True)
            plt.show()
        else:
            print("plot not available")
        exit(1)

    return None


def UploadStatus(report_interval):
    def filter(new_buf):
        filter.currentbytes += len(new_buf)
        if filter.currentbytes - filter.lastreport > report_interval:
            print('.', end='', flush=True)
            filter.lastreport = filter.currentbytes
    filter.currentbytes = 0
    filter.lastreport = 0
    return filter

def host_pull(args, uut, shot):
    # set up a RawClient to pull data from the mgtdram host_pull port.
    rc = uut.create_mgtdram_pull_client()
    first_run = True
    nchan = int(uut.s0.NCHAN)
    group = 12 if nchan%3 == 0 else 16
    if args.offloadblocks_count%group != 0:
        nblocks = (args.offloadblocks_count//group + 1)*group
    else:
        nblocks = args.offloadblocks_count

    nbytes = nblocks*MGT_BLOCK_BYTES
    nread = 0
    _data_size = uut.data_size()
    bn = 0                          # block number. redundant, there will be only one block.

    print("Starting host pull {} bytes now data size {}".format(nbytes, _data_size))

    for buffer in rc.get_blocks(nbytes, data_size=_data_size):

        if first_run:
            good_data = buffer
            first_run = False

        if args.save_data == 1:
            fn = "./{}/{:04d}.dat".format(args.uut[0], shot)
            make_data_dir(args.uut[0], 0)
            buffer.tofile(fn)
            print("{}".format(fn))
        else:
            print("Block {} pulled, size bytes : {}.".format(bn, buffer.size))

        if args.validate != 'no':
            validate_streamed_data(good_data, buffer, bn)

        bn += 1
        nread += len(buffer) * _data_size
        if nread >= nbytes:
            break

    if len(buffer) == 0:
        print("Data offload failed.")
        print("Pulled {} blocks.".format(bn))
        exit(1)

    logprint("Data offloaded {} blocks {}".format(
        bn, "" if args.validate == 'no' else "and all data validation passed."))
    return nread


def write_console(message):
    # explicit flush needed to avoid lockup on Windows.
    sys.stdout.write(message)
    sys.stdout.flush()


class UploadFilter:
    def __init__(self):
        self.okregex = re.compile(r"axi0 start OK ([0-9]{4}) OK")
        self.line = 0

    def __call__(self, st):
        st = st.rstrip()
        LOG.write("{}\n".format(st))

        if self.okregex.search(st) != None:
            if self.line % 10 != 0:
                write_console('.')
            else:
                write_console("{}".format(self.line/10))
            self.line += 1
            if self.line > 100:
                write_console('\n')
                self.line = 0
        else:
            if self.line != 0:
                write_console('\n')
            write_console(">{}\n".format(st))
            self.line = 0


def run_shot(uut, args):
    # always capture over. The offload is zero based anyway, so add another one
    if args.captureblocks:
        uut.s14.mgt_run_shot = str(int(args.captureblocks) + 2)
        uut.run_mgt()
     
def run_offload(uut, args, shot):        
    if args.host_pull == 1:
        # for loop in list(range(1, args.loop + 1)):
        return host_pull(args, uut, shot)

    else:
        uut.s14.mgt_offload = args.offloadblocks if args.offloadblocks != 'capture' \
            else '0-{}'.format(args.captureblocks)
        t1 = datetime.datetime.now()
        uut.run_mgt(UploadFilter())
        ttime = datetime.datetime.now()-t1

        if args.validate != 'no':
            cmd = "{} {}".format(args.validate, uut.uut)
            print("run \"{}\"".format(cmd))
            rc = call(cmd, shell=True, stdin=0, stdout=1, stderr=2)
            if rc != 0:
                print("ERROR called process {} returned {}".format(
                    args.validate, rc))
                exit(1)
        return args.captureblocks*MGT_BLOCK_BYTES

def run_shots(args):
    global LOG
    global _logprint
    _logprint = args.logprint
    global uut_name
    uut_name = args.uut[0]
    nbytes = 0

    LOG = open("mgtdramshot-{}.log".format(args.uut[0]), "w")
    uut = acq400_hapi.Acq2106_Mgtdram8(args.uut[0])
    acq400_hapi.Acq400UI.exec_args(uut, args)

    if args.offloadblocks != 'capture':
        args.offloadblocks_count = int(args.offloadblocks)
    elif args.captureblocks != 0:
        args.offloadblocks_count = args.captureblocks
    else:
        args.offloadblocks_count = acq400_hapi.Acq400.intpv(uut.s0.BLT_BUFFERS_M)
        print("offload {} buffers from uut".format(args.offloadblocks_count))
    
    uut.s14.mgt_taskset = '1'
    if args.validate != 'no':
        for s in uut.modules:
            uut.modules[s].simulate = 1
    try:
        actions=""
        if args.captureblocks != 0:
            actions = "cap"
        if args.offloadblocks_count != 0:
            if len(actions):
                 actions = "{}+{}".format(actions, "offload")
            else:
                 actions = "offload"

        for shot in range(0, args.loop):
            t1 = datetime.datetime.now()
            print("shot: {} {}".format(shot, t1.strftime("%Y%m%d %H:%M:%S")))
            mbps=""
            if args.captureblocks != 0:
                run_shot(uut, args)
            if args.offloadblocks_count != 0:
                nbytes = run_offload(uut, args, shot)
            t2 = datetime.datetime.now()
            et = (t2-t1).seconds
            if nbytes:
                mb = nbytes/0x100000
                mbps = "offload {} MB, {:.2f} MB/s".format(mb, mb/et)
            print("shot: {} {} done in {} seconds {}\n\n".format(shot, actions, et, mbps))

            if args.wait_user:
                input("hit return to continue")
    except KeyboardInterrupt:
        print("Keyboard Interrupt, take it all down NOW")
        os._exit(1)

    os._exit(0)


def run_main():
    parser = argparse.ArgumentParser(description='acq2106 mgtdram test')
    acq400_hapi.Acq400UI.add_args(parser)
    parser.add_argument('--loop', type=int, default=1, help="loop count")
    parser.add_argument('--captureblocks', type=int,
                        default="2000", help='number of 4MB blocks to capture')
    parser.add_argument('--offloadblocks', type=str,
                        default="capture", help='block list to upload nnn-nnn')
    parser.add_argument('--validate', type=str, default='no',
                        help='program to validate data')
    parser.add_argument('--wait_user', type=int, default=0,
                        help='1: force user input each shot')

    parser.add_argument('--host_pull', type=int, default=1,
                        help='Whether or not to use the HOST PULL method. Default: 1.')

    parser.add_argument('--save_data', type=int, default=1,
                        help='Whether or not to save data to a file in 4MB chunks. Default: 0.')

    parser.add_argument('--logprint', type=int, default=1,
                              help='1: Print log messages. '
                              '2: Save reduced log to log file.')

    parser.add_argument('uut', nargs=1, help="uut ")
    run_shots(parser.parse_args())

# execution starts here


if __name__ == '__main__':
    run_main()
