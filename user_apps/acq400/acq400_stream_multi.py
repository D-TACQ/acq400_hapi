#!/usr/bin/env python3

"""
This is a script intended to connect to a UUT and stream data from port 4210.

The data that has been streamed is not demuxed and so if it is to be used then it has to be demuxed first.
Something like:

    >>> data = numpy.fromfile("0000", dtype="<datatype>")
    >>> plt.plot(data[::<number of channels>])
    >>> plt.show()

usage::
    acq400_stream.py [-h] [--filesize FILESIZE] [--totaldata TOTALDATA]
                        [--root ROOT] [--runtime RUNTIME] [--verbose VERBOSE]
                        uuts [uuts ...]

acq400 stream

positional arguments:
  uuts                  uuts

optional arguments:
  -h, --help            show this help message and exit
  --filesize FILESIZE   Size of file to store in KB. If filesize > total data
                        then no data will be stored.
  --totaldata TOTALDATA
                        Total amount of data to store in KB
  --root ROOT           Location to save files
  --runtime RUNTIME     How long to stream data for
  --verbose VERBOSE     Prints status messages as the stream is running


Some usage examples are included below:

1: Acquire files of size 1024kb up to a total of 4096kb:


    >>> python acq400_stream.py --verbose=1 --filesize=1M --totaldata=4M <module ip or name>

2: Acquire a single file of size 4096kb:


    >>> python acq400_stream.py --verbose=1 --filesize=4M --totaldata=4M <module ip or name>

3: Acquire files of size 1024 for 10 seconds:


    >>> python acq400_stream.py --verbose=1 --filesize=1M --runtime=10 <module ip or name>

4: Acquire data for 5 seconds and write the data all to a single file:


    >>> python acq400_stream.py --verbose=1 --filesize=9999M --runtime=5 <module ip or name>

"""

import acq400_hapi
import numpy as np
import os
import time
import argparse
import sys
import signal
import shutil
from acq400_hapi.acq400_print import DISPLAY

import multiprocessing as MP
import threading

def make_data_dir(directory, verbose):
    if verbose > 2:
        print("make_data_dir {}".format(directory))
    try:
        os.makedirs(directory)
    except Exception:
        if verbose > 2:
            print("Directory already exists")
        pass

def remove_stale_data(args):
    for uut in args.uuts:
        path = os.path.join(args.root, uut)
        if os.path.exists(path):
            if args.force_delete:
                pass
            else:
                answer = input("Stale data detected. Delete all contents in " + args.root + str(args.uuts[0]) + "? y/n ")
                if answer != 'y':
                    continue
            if args.verbose:
                print("removing {}".format(path))
            shutil.rmtree(path)

def self_burst_trigger_callback(uut, job):
    def cb(fn):
        if job:
            os.system(f'{job} {fn}')
            for line in sys.stdin:
                if line.startswith('q'):
                    uut.s0.set_abort = 1
                    uut.close()
                    sys.exit(0)
                else:
                    break
        uut.s0.soft_trigger = 1
    return cb

def self_start_trigger_callback(uut):
    def cb():
        print("self_start_trigger_callback")
        while uut.s0.state.split(' ')[0] != '1':
            time.sleep(0.5)
        uut.s0.soft_trigger = 1
    return cb

class StreamsOne:

    class pipe_conn:
        def __init__(self, pipe):
            self.pipe = pipe
            self.status = {
                'state' : None,
                'stopped' : False,
            }

        def send(self):
            self.pipe.send(self.status)

        def set(self, key, value):
            self.status[key] = value

    def __init__ (self, args, uut_name, halt, pipe, delay):
        self.args = args
        self.uut_name = uut_name
        self.halt = halt
        self.delay = delay
        self.status = self.pipe_conn(pipe)
        self.log_file = f"{uut_name}_times.log"
        open(self.log_file, 'w').close()

    def logtime(self, t0, t1):
        with open(self.log_file, 'a') as f:
            f.write(f"{int((t1-t0) * 1000)}\n")
        return t1
    
    def update_status_forever(self):
        while True:
            self.status.set('state', acq400_hapi.pv(self.uut.s0.CONTINUOUS_STATE))
            self.status.send()
            time.sleep(1)

    def stop_proccess(self, reason):
        self.status.set('stopped', True)
        self.uut.stream_close()
        self.halt.wait()
        exit(reason)

    def run(self, callback=None):

        self.uut = acq400_hapi.factory(self.uut_name)
        threading.Thread(target=self.update_status_forever, daemon=True).start()
        time.sleep(self.delay)
        cycle = -1
        fnum = 999       # force initial directory create
        data_bytes = 0
        files = 0

        signal.signal(signal.SIGINT, signal.SIG_IGN)

        if callback is None:
            callback = lambda _clidata: False

        if self.args.burst_on_demand:
            self.uut.s1.rgm='3,1,1'
            bod_def = self.args.burst_on_demand.split(',')
            bod_len = int(bod_def[0])
            bod_job = None
            if len(bod_def) == 2:
                bod_job = bod_def[1]
            self.uut.s1.RTM_TRANSLEN = bod_len
            self.args.filesamples = bod_len
            if self.args.trigger_from_here != 0:
                callback = self_burst_trigger_callback(self.uut, bod_job)
                self.thread = threading.Thread(target=self_start_trigger_callback(self.uut))
                self.thread.daemon = True
                self.thread.start()


        try:
            if int(self.uut.s0.data32):
                data_size = 4
                wordsizetype = "<i4"  # 32 bit little endian
            else:
                wordsizetype = "<i2"  # 16 bit little endian
                data_size = 2
        except AttributeError:
            print("Attribute error detected. No data32 attribute - defaulting to 16 bit")
            wordsizetype = "<i2"  # 16 bit little endian
            data_size = 2

        netssb = int(self.uut.s0.ssb)
        if self.args.subset:
            c1,clen = [ int(x) for x in self.args.subset.split(',')]
            netssb = clen * data_size

        if self.args.filesamples:
            self.args.filesize = self.args.filesamples*netssb

        blen = self.args.filesize//data_size

        if self.args.burst_on_demand and self.args.verbose:
            print(f'burst_on_demand RTM_TRANSLEN={self.args.burst_on_demand} netssb={netssb} filesize={self.args.filesize} blen={blen}')

        t_run = 0
        fn = "no-file"

        for buf in self.uut.stream(recvlen=blen, data_size=data_size):

            if self.halt.is_set():
                self.stop_proccess(f"{self.uut_name} Stopped")

            if data_bytes == 0:
                t0 = time.time()
            else:
                t_run = self.logtime(t0, time.time()) - t0

            data_bytes += len(buf) * data_size

            if len(buf) == 0:
                print("Zero length buffer, quit")
                return
            
            self.status.set('runtime', f"{t_run:.0f}s")
            self.status.set('total bytes', f"{data_bytes}")
            self.status.set('rate', f"{data_bytes / t_run / 0x100000  if t_run else 0:.2f}MB/s")
            self.status.set('files', f"{files}")

            if not self.args.nowrite:
                if fnum >= self.args.files_per_cycle:
                    fnum = 0
                    cycle += 1
                    root = os.path.join(self.args.root, self.uut_name, "{:06d}".format(cycle))
                    make_data_dir(root, self.args.verbose)

                fn = os.path.join(root, "{:04d}.dat".format(fnum))
                data_file = open(fn, "wb")
                buf.tofile(data_file, '')
                files += 1
                if self.args.verbose > 3:
                    print(f'wrote file: {fn}')

            if self.args.verbose == 0:
                pass
            elif self.args.verbose == 1:
                pass
            if not self.args.display and self.args.verbose > 2:
                if t_run > 0:
                    print("{:8.3f} {} files {:4d} total bytes: {:10d} data bytes: {} rate: {:.2f} MB/s".
                            format(t_run, fn, files, int(data_bytes), int(data_bytes), data_bytes/t_run/0x100000))
            fnum += 1

            if callback(fn) or t_run >= self.args.runtime or data_bytes > self.args.totaldata:
                break
        
        self.stop_proccess(f"{self.uut_name} Finished")

def status_cb():
    print("Another one")

def run_stream_run(args):

    def wrapper(args, uut, halt, pipe, delay):
        streamer = StreamsOne(args, uut, halt, pipe, delay)
        streamer.run()

    recvs = {}
    pss = {}
    delay = 2
    halt = MP.Event()
    for uut in args.uuts:
        recv, pipe = MP.Pipe()
        recvs[uut] = recv
        pss[uut] = MP.Process(target=wrapper, args=(args, uut, halt, pipe, delay,), daemon=False)
        pss[uut].start()
        delay = 0

    D = DISPLAY()
    uut_status = {}
    start_time = time.time()
    try:
        while True:
            stopped = 0
            for uut_name, ps in pss.items():
                while recvs[uut_name].poll():
                    try:
                        uut_status[uut_name] = recvs[uut_name].recv()
                    except EOFError:
                        try:
                            uut_status[uut_name]['state'] = 'DEAD'
                        except:
                            pass
            D.add_line("")
            D.add_line(f"{{BOLD}}Stream Multi {{RESET}}Runtime: {round(time.time() - start_time)}s")
            for uut, status in uut_status.items():
                if status['stopped']:
                    stopped += 1
                D.add(f"{{REVERSE}}{uut}{{RESET}} ")
                for key, value in status.items():
                    D.add(f"{{BOLD}}{key}{{RESET}}[{value}] ")
                D.end()

            if stopped == len(pss):
                halt.set()
                D.render(False)
                break
            if args.display:
                D.render()
            D.buffer = ''
            time.sleep(1)

    except KeyboardInterrupt:
        D.render_interrupted()
        halt.set()
        print('Keyboard Interrupt')
    print('Done')

def run_stream_prep(args):
    if args.filesize > args.totaldata:
            args.filesize = args.totaldata
    remove_stale_data(args)
    return args

def get_parser(parser=None):
    if not parser:
        is_client = True        
        parser = argparse.ArgumentParser(description='acq400 stream')
        parser.add_argument('--callback', default=None, help='not for users, client programs can install a callback here')
    else:
        is_client = False
        
    #parser.add_argument('--filesize', default=1048576, type=int,
    #                    help="Size of file to store in KB. If filesize > total data then no data will be stored.")
    parser.add_argument('--burst_on_demand', default=None, type=str, help="Burst Size in Samples[,./plotjob]")
    parser.add_argument('--trigger_from_here', default=0, type=int, help="action soft trigger from this application")
    parser.add_argument('--subset', default=None, help='subset command if present eg 1,5 :: strips first 5 channels')
    parser.add_argument('--filesize', default=0x100000, action=acq400_hapi.intSIAction, decimal=False, help="file size in bytes")
    parser.add_argument('--filesamples', default=None, action=acq400_hapi.intSIAction, decimal=False, help="file size in samples (overrides filesize)")
    parser.add_argument('--files_per_cycle', default=100, type=int, help="files per cycle (directory)")
    parser.add_argument('--force_delete', default=0, type=int, help="silently delete any existing data files")
    parser.add_argument('--nowrite', default=0, help="do not write file")
    parser.add_argument('--totaldata', default=10000000000, action=acq400_hapi.intSIAction, decimal = False)
    #parser.add_argument('--totaldata', default=4194304, type=int, help="Total amount of data to store in KB")
    parser.add_argument('--root', default="", type=str, help="Location to save files. Default dir is UUT name.")
    parser.add_argument('--runtime', default=1000000, type=int, help="How long to stream data for")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the stream is running')
    parser.add_argument('--display', default=1, type=int, help='Render display')
    if is_client:
        parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

def run_stream(args):
    run_stream_prep(args)
    run_stream_run(args)

def run_main():
    run_stream(get_parser().parse_args())


if __name__ == '__main__':
    run_main()
