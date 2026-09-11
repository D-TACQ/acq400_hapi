#!/usr/bin/env python3

"""Stream data from one or more ACQ400 UUTs over port 4210.

Data streamed from port 4210 is multiplexed binary data across all active channels.
To analyze or plot the data, demux by channel count:

    >>> data = numpy.fromfile("0000.dat", dtype="<i2")
    >>> ch1 = data[0::<number of channels>]
    >>> plt.plot(ch1)
    >>> plt.show()

Data Sizing & Counting Arguments:
    --filesamples  : File size in samples (default: 100k). Guarantees integer
                     sample frame alignment and prevents channel shifting.
    --totalsamples : Total samples to capture across all channels.
    --totalfiles   : Total number of files/buffers to capture.
    --runtime      : Duration in seconds. Timer starts only once data flows
                     and completes the active buffer (pessimistic timing).
    --combine      : Combines all files within each cycle directory into a
                     single continuous file (e.g. 0000-0100.dat).

Usage Examples:
    1: Acquire 100k samples per file for 10 seconds:
        python acq400_stream_multi.py --filesamples=100k --runtime=10 uut1

    2: Acquire 100k samples per file up to a total of 1M samples:
        python acq400_stream_multi.py --filesamples=100k --totalsamples=1M uut1

    3: Stream multiple UUTs concurrently (comma or space separated), combining cycle files:
        python acq400_stream_multi.py --filesamples=100k --combine=1 --runtime=30 uut1,uut2

    4: Capture exactly 50 files of 50k samples each:
        python acq400_stream_multi.py --filesamples=50k --totalfiles=50 uut1
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
                answer = input(f"Stale data detected. Delete all contents in {path}? y/n ")
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
                'data_flowing' : False,
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
        self.previous = None
        self.log_file = os.path.join(args.root, f"{uut_name}_times.log")
        open(self.log_file, 'w').close()

    def logtime(self, t0, t1):
        if not self.previous:
            self.previous = t1
        with open(self.log_file, 'a') as f:
            f.write(f"{int((t1 - t0) * 1000)} {int((t1 - self.previous) * 1000 )}\n")
        self.previous = t1
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
        total_samples = 0
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

        blen = self.args.filesamples * (netssb // data_size)

        if self.args.burst_on_demand and self.args.verbose:
            print(f'burst_on_demand RTM_TRANSLEN={self.args.burst_on_demand} netssb={netssb} filesamples={self.args.filesamples} blen={blen}')

        t0 = None
        t_run = 0
        fn = "no-file"
        data_file = None

        try:
            for buf in self.uut.stream(recvlen=blen, data_size=data_size):

                if self.halt.is_set():
                    self.stop_proccess(f"{self.uut_name} Stopped")

                now = time.time()
                if t0 is None:
                    # Clock only begins once the first data buffer has been received
                    t0 = now
                    self.status.set('data_flowing', True)
                else:
                    t_run = self.logtime(t0, now) - t0

                total_samples += self.args.filesamples
                data_bytes = total_samples * netssb

                if len(buf) == 0:
                    print("Zero length buffer, quit")
                    return
                
                self.status.set('runtime', f"{t_run:.0f}s")
                self.status.set('samples', f"{total_samples}")
                self.status.set('rate', f"{data_bytes / t_run / 0x100000 if t_run else 0:.2f}MB/s")
                self.status.set('files', f"{files}")

                if not self.args.nowrite:
                    if fnum >= self.args.files_per_cycle:
                        fnum = 0
                        cycle += 1
                        if data_file:
                            data_file.close()
                            data_file = None
                        root = os.path.join(self.args.root, self.uut_name, "{:06d}".format(cycle))
                        make_data_dir(root, self.args.verbose)
                    
                    if not self.args.combine:
                        fn = os.path.join(root, f"{fnum:04d}.dat")
                        with open(fn, 'wb') as data_file:
                            buf.tofile(data_file)
                        data_file = None
                        files += 1
                    else:
                        if not data_file:
                            fn = os.path.join(root, f"{0:04d}-{self.args.files_per_cycle:04d}.dat")
                            data_file = open(fn, "wb")
                            files += 1
                        buf.tofile(data_file)

                if self.args.verbose == 0:
                    pass
                elif self.args.verbose == 1:
                    pass
                if not self.args.display and self.args.verbose > 2:
                    if t_run > 0:
                        print("{:8.3f} {} files {:4d} total samples: {:10d} bytes: {} rate: {:.2f} MB/s".
                                format(t_run, fn, files, total_samples, data_bytes, data_bytes/t_run/0x100000))
                fnum += 1

                # Pessimistic exit: current full buffer is committed to disk before stopping
                if callback(fn):
                    break
                if self.args.runtime is not None and t_run >= self.args.runtime:
                    break
                if self.args.totalsamples is not None and total_samples >= self.args.totalsamples:
                    break
                if self.args.totalfiles is not None and files >= self.args.totalfiles:
                    break
        finally:
            if data_file:
                data_file.close()
                data_file = None
        
        self.stop_proccess(f"{self.uut_name} Finished")

def status_cb():
    print("Another one")

def wrapper(args, uut, halt, pipe, delay):
    streamer = StreamsOne(args, uut, halt, pipe, delay)
    streamer.run()

def run_stream_run(args):
    fixup_uuts(args)
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
    data_start_time = None
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

            if data_start_time is None:
                for status in uut_status.values():
                    if status.get('data_flowing'):
                        data_start_time = time.time()
                        break

            D.add_line("")
            if data_start_time is not None:
                runtime_str = f"{round(time.time() - data_start_time)}s"
            else:
                runtime_str = "Waiting for data..."
            D.add_line(f"{{BOLD}}Stream Multi {{RESET}}Runtime: {runtime_str}")
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

def fixup_uuts(args):
    if hasattr(args, 'uuts') and args.uuts:
        if isinstance(args.uuts, str):
            args.uuts = [args.uuts]
        args.uuts = [u.strip() for item in args.uuts for u in item.split(',') if u.strip()]
    return args

def run_stream_prep(args):
    fixup_uuts(args)
    remove_stale_data(args)
    if args.root and not os.path.exists(args.root):
        os.makedirs(args.root)
    return args

def get_parser(parser=None):
    if not parser:
        is_client = True        
        parser = argparse.ArgumentParser(description='Stream data from multiple UUTs')
        parser.add_argument('--callback', default=None, help='not for users, client programs can install a callback here')
    else:
        is_client = False

    data_group = parser.add_argument_group('Data sizing & stopping criteria')
    data_group.add_argument('--filesamples', default=100000, action=acq400_hapi.intSIAction, decimal=False,
                            help="File size in samples (default: 100k)")
    data_group.add_argument('--totalsamples', default=None, action=acq400_hapi.intSIAction, decimal=False,
                            help="Total samples to capture across run")
    data_group.add_argument('--totalfiles', default=None, type=int,
                            help="Total file chunks to capture")
    data_group.add_argument('--runtime', default=None, type=int,
                            help="Capture duration in seconds (timer begins when data flows, pessimistic)")

    storage_group = parser.add_argument_group('Cycle & file organization')
    storage_group.add_argument('--files_per_cycle', default=100, type=int,
                               help="Files per cycle directory (default: 100)")
    storage_group.add_argument('--combine', default=0, type=int,
                               help="Combine cycle files into a single continuous file per cycle (default: 0)")
    storage_group.add_argument('--root', default="", type=str,
                               help="Location to save files (default: UUT name)")

    trigger_group = parser.add_argument_group('Trigger & burst options')
    trigger_group.add_argument('--burst_on_demand', default=None, type=str,
                               help="Burst Size in Samples[,./plotjob]")
    trigger_group.add_argument('--trigger_from_here', default=0, type=int,
                               help="Action soft trigger from this application")
    trigger_group.add_argument('--subset', default=None,
                               help="Subset command if present eg 1,5 :: strips first 5 channels")

    control_group = parser.add_argument_group('Execution & display control')
    control_group.add_argument('--force_delete', default=0, type=int,
                               help="Silently delete any existing data files")
    control_group.add_argument('--nowrite', default=0,
                               help="Do not write files to disk")
    control_group.add_argument('--verbose', default=0, type=int,
                               help="Prints status messages as the stream is running")
    control_group.add_argument('--display', default=1, type=int,
                               help="Render interactive status display")

    if is_client:
        parser.add_argument('uuts', nargs='+', help="UUT hostname(s) or IP address(es) (space- or comma-separated)")
    return parser

def run_stream(args):
    run_stream_prep(args)
    run_stream_run(args)

if __name__ == '__main__':
    run_stream(get_parser().parse_args())
