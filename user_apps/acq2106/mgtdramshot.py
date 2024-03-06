#!/usr/bin/env python
""" mgtdramshot.py Capture to MGTDRAM

- optional capture to mgtdram
- manage upload
- optional validation

assumes that clocking has been pre-assigned.

example usage::

       ./mgtdramshot.py --loop=100 --simulate=1 --validate=validate-6x480 --captureblocks=2000 --offloadblocks=0-1999 acq2106_007

.. rst-class:: hidden
    
    usage: mgtdramshot.py [-h] [--clk CLK] [--trg TRG] [--sim SIM] [--trace TRACE]
                        [--auto_soft_trigger AUTO_SOFT_TRIGGER]
                        [--clear_counters] [--loop LOOP]
                        [--captureblocks CAPTUREBLOCKS]
                        [--offloadblocks OFFLOADBLOCKS] [--validate VALIDATE]
                        [--wait_user WAIT_USER] [--wait_shot WAIT_SHOT]
                        [--save_data SAVE_DATA] [--shot SHOT] [--twa TWA]
                        [--logprint LOGPRINT]
                        uuts [uuts ...]

    acq2106 mgtdram test

    positional arguments:
    uuts                  uut

    optional arguments:
    -h, --help            show this help message and exit
    --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
    --trg TRG             int|ext,rising|falling
    --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
    --trace TRACE         1 : enable command tracing
    --auto_soft_trigger AUTO_SOFT_TRIGGER  force soft trigger generation
    --clear_counters      clear all counters SLOW
    --loop LOOP           loop count
    --captureblocks CAPTUREBLOCKS  number of 4MB blocks to capture
    --offloadblocks OFFLOADBLOCKS  block list to upload nnn-nnn
    --validate VALIDATE   program to validate data
    --wait_user WAIT_USER  1: force user input each shot
    --wait_shot WAIT_SHOT  1: wait for some external agent to run the shot, then offload all
    --save_data SAVE_DATA  Whether or not to save data to a file in 4MB chunks. Default: 1
    --shot SHOT           set a shot number
    --twa TWA             trigger_when_armed
    --logprint LOGPRINT   1: Print log messages. 2: Save reduced log to log file.

"""

import sys
import datetime
import acq400_hapi
import argparse
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

import multiprocessing as mp
from threading import Thread

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
    uut_name = uut.uut
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
    bn = 0 
                             # block number. redundant, there will be only one block.
    buffer = None

    print("Starting host pull {} bytes now data size {}".format(nbytes, _data_size))

    for buffer in rc.get_blocks(nbytes, data_size=_data_size):

        if first_run:
            good_data = buffer
            first_run = False

        if args.save_data == 1:
            if args.overwrite:
                shot = 0
            fn = "./{}/{:04d}.dat".format(uut_name, shot)
            make_data_dir(uut_name, 0)
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

    if buffer is None or len(buffer) == 0:
        print("Data offload failed.")
        print("Pulled {} blocks.".format(bn))
        exit(1)


    rc.sock.close()
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

class AtFilter:
    def __init__(self):
        self.filter_regex_set = (re.compile(r"@@@"), re.compile(r"process"), re.compile(r"log file"))


    def __call__(self, st):
        st = st.rstrip()
      
        for f in self.filter_regex_set:
            if f.search(st) != None:
                return
        write_console("{}\n".format(st))

def run_shot(uut, args):
    # always capture over. The offload is zero based anyway, so add another one
    uut.s14.mgt_run_shot = args.captureblocks
    if args.siggen:
        Thread(target=trigger_on_arm, args=(uut, args.siggen)).start()
    uut.run_mgt(AtFilter())
    return int(uut.s1.shot)

def trigger_on_arm(uut, siggen):
    """trigger siggen when uut reaches arm"""
    while acq400_hapi.pv(uut.s0.CONTINUOUS_STATE) != 'ARM':
        time.sleep(1)
    acq400_hapi.Agilent33210A(siggen).trigger()

def wait_shot(uut, args):  
    if args.offloadblocks != 'capture': 
        args.offloadblocks_count = acq400_hapi.intpv(uut.s0.BLT_BUFFERS_M)
    uut.run_mgt(AtFilter(), set_arm=False)
    return int(uut.s1.shot)
        
     
def run_offload(uut, args, shot):
    return host_pull(args, uut, shot)        

def run_shots(args):
    global LOG
    global _logprint
#    print("run_shots {}".format(args))
    _logprint = args.logprint
    global uut_name
    uut_name = args.uut
    nbytes = 0

    print("run_shots {}".format(uut_name))
    LOG = open("mgtdramshot-{}.log".format(uut_name), "w")
    uut = acq400_hapi.Acq2106_Mgtdram8(args.uut)
    acq400_hapi.Acq400UI.exec_args(uut, args)

    if args.captureblocks != 0:
        uut.s0.BLT_BUFFERS = args.captureblocks
        args.captureblocks = acq400_hapi.intpv(uut.s0.BLT_BUFFERS_M)

    if args.offloadblocks != 'capture':
        args.offloadblocks_count = int(args.offloadblocks)
    else:
        args.offloadblocks_count = acq400_hapi.intpv(uut.s0.BLT_BUFFERS_M)
        print("offload {} buffers from uut".format(args.offloadblocks_count))
    
    uut.s14.mgt_taskset = '1'
    if args.validate == 'yes' or args.validate == '1':
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
            shot_number = shot
            t1 = datetime.datetime.now()
            print("shot: {} {}".format(shot, t1.strftime("%Y%m%d %H:%M:%S")))
            mbps=""
            if args.captureblocks != 0:
                shot_number = run_shot(uut, args)
            elif args.wait_shot:
                shot_number = wait_shot(uut, args)
            if args.offloadblocks_count != 0:
                nbytes = run_offload(uut, args, shot_number)
            t2 = datetime.datetime.now()
            et = (t2-t1).seconds
            if nbytes:
                mb = nbytes/0x100000
                mbps = "offload {} MB, {:.2f} MB/s".format(mb, mb/et)
            print("shot: {} {} done in {} seconds {}\n\n".format(shot_number, actions, et, mbps))

            if args.wait_user:
                input("hit return to continue")
    except KeyboardInterrupt:
        print("Keyboard Interrupt, take it all down NOW")
        os._exit(1)

    os._exit(0)

def run_shots1(targs):
    sys.stdout = open("mgtdram_{}.log".format(targs.uut), "a")
    return run_shots(targs)

import copy

def trigger_when_armed(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uuts]
    top = uuts[0]
        
    all_armed = False
    time.sleep(5)
    while not all_armed:
        print("checking")
        #armed = [ acq400_hapi.Acq400.pv(u.s0.BLT_ACT_STATE) for u in uuts ]
        armed = [ u.s0.BLT_ACT_STATE for u in uuts ]        
        print("hello {}".format(armed))
        arm_count = 0
        for s in armed:
            if s.find("ARM") != -1:
                arm_count += 1
                  
        if arm_count == len(args.uuts):
            all_armed = True
        else:
            time.sleep(0.5)
     
    top.s0.SIG_SRC_TRG_0 = 'EXT'    

def prep_many(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uuts]
    top = uuts[0]
    
    if args.shot is not None:
        for u in uuts:
            u.s1.shot = args.shot
    top.s0.SIG_SRC_TRG_0 = 'NONE'
    top.s0.SIG_SYNC_OUT_TRG_DX = 'd0'
        
def control_many(args):
    prep_many(args)
    ps = []
#    ps = [mp.Process(target=trigger_when_armed, args=(args,))]
    u_args = [ copy.copy(args) for u in args.uuts ]
    for ix, u in enumerate(args.uuts):
        u_args[ix].uut = u
        print("ps.append {} {}".format(ix, u))
        ps.append(mp.Process(target=run_shots1, args=(u_args[ix],)))
         
    print("start me up")
    
    for p in ps:
        p.start()

    print("all started")
   
    for p in ps:
        p.join()

def run_main(args):
    if args.wait_shot > 0:
        args.captureblocks = 0
       
    if args.twa:
        trigger_when_armed(args)
    elif len(args.uuts) > 1:
        control_many(args)
    else:
        args.uut = args.uuts[0]
        run_shots(args)

def get_parser():
    parser = argparse.ArgumentParser(description='mgtdram test')
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
    parser.add_argument('--wait_shot', type=int, default=0,
                        help="1: wait for some external agent to run the shot, then offload all")
    parser.add_argument('--save_data', type=int, default=1,
                        help='Whether or not to save data to a file in 4MB chunks. Default: 1')
    parser.add_argument('--shot', type=int, default=None, help="set a shot number")
    parser.add_argument('--twa', type=int, default=None, help="trigger_when_armed")
    parser.add_argument('--overwrite', type=int, default=0, help="0: new file per shot 1: same file per shot")
    parser.add_argument('--siggen', default=None, help="siggen hostname to trigger when armed")

    parser.add_argument('--logprint', type=int, default=1,
                              help='1: Print log messages. '
                              '2: Save reduced log to log file.')
    parser.add_argument('uuts', nargs='+', help="uut ")
    return parser
    
# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())
