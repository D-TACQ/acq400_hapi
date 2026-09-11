#!/usr/bin/env python3

"""
acq400_stream_awg.py Stream AWG data to multiple UUTs concurrently

USAGE EXAMPLES:
    ./acq400_stream_awg.py --file=../acq400_chapi/NEC14_patterns/ --repeat=1 acq1102_072,acq1102_073
    ./acq400_stream_awg.py --file=data.bin --reps=5 acq1102_072:54207 acq1102_073:54207
"""

import acq400_hapi
from acq400_hapi import netclient
import argparse
import sys
import threading
import os
import time
import glob
import signal

class UUTStreamer(threading.Thread):
    def __init__(self, target_spec, file_list, repeat=False, reps=0, soft_trigger=0):
        super().__init__()
        self.daemon = True  # Allows immediate termination on Ctrl+C
        
        # Parse target and optional port (Default: 54207 to match C++ acq400_chapi)
        parts = target_spec.split(':')
        self.host = parts[0]
        self.port = int(parts[1]) if len(parts) > 1 else 54207
        
        self.file_list = file_list
        self.repeat = repeat
        self.reps = reps
        self.soft_trigger = soft_trigger
        
        self.bytes_sent = 0
        self.active = True
        self.nc = None

    def stop(self):
        """ Force-stop worker loop and close open socket """
        self.active = False
        if self.nc and hasattr(self.nc, 'sock') and self.nc.sock:
            try:
                self.nc.sock.close()
            except Exception:
                pass

    def read_file_chunks(self, filepath, chunk_size=0x10000):
        """ Yield binary chunks from file """
        with open(filepath, "rb") as fp:
            while self.active:
                data = fp.read(chunk_size)
                if not data:
                    break
                yield data

    def run(self):
        try:
            uut = acq400_hapi.Acq400(self.host)
            
            if self.soft_trigger:
                uut.s0.soft_trigger = 1

            rep_count = 0
            with netclient.Netclient(self.host, self.port) as nc:
                self.nc = nc
                while self.active:
                    for filepath in self.file_list:
                        if not self.active:
                            break
                        for chunk in self.read_file_chunks(filepath):
                            if not self.active:
                                break
                            nc.sock.sendall(chunk)
                            self.bytes_sent += len(chunk)
                    
                    rep_count += 1
                    if self.reps > 0 and rep_count >= self.reps:
                        break
                    if not self.repeat and self.reps == 0:
                        break

        except Exception as e:
            if self.active:
                print(f"\n[ERROR] {self.host}: {e}", file=sys.stderr)
        finally:
            self.active = False

def monitor(streamers):
    """ Periodically reports aggregated bandwidth across all active threads """
    last_bytes = {s.host: 0 for s in streamers}
    start_time = time.time()
    
    while any(s.is_alive() for s in streamers):
        time.sleep(0.5)
        now = time.time()
        dt = now - start_time
        start_time = now
        if dt <= 0:
            dt = 1.0
        
        rates = []
        for s in streamers:
            delta = s.bytes_sent - last_bytes[s.host]
            last_bytes[s.host] = s.bytes_sent
            rate_mb = (delta / dt) / (1024 * 1024)
            rates.append(f"{s.host}: {rate_mb:.2f} MB/s")
        
        sys.stderr.write("\r" + " | ".join(rates) + "     ")
        sys.stderr.flush()

def resolve_files(file_args):
    """ Resolves directory paths, glob patterns (*), and comma-separated file strings """
    resolved_files = []
    tokens = [t.strip() for t in file_args.split(',') if t.strip()]
    
    for token in tokens:
        if os.path.isdir(token):
            dir_files = sorted([
                os.path.join(token, f) for f in os.listdir(token)
                if os.path.isfile(os.path.join(token, f))
            ])
            resolved_files.extend(dir_files)
            
        elif '*' in token or '?' in token:
            matched = sorted(glob.glob(token))
            resolved_files.extend([f for f in matched if os.path.isfile(f)])
            
        elif os.path.isfile(token):
            resolved_files.append(token)
            
        else:
            print(f"ERROR: File, pattern, or directory not found: {token}", file=sys.stderr)
            sys.exit(1)

    if not resolved_files:
        print(f"ERROR: No valid files found matching input: {file_args}", file=sys.stderr)
        sys.exit(1)

    return resolved_files

def get_parser():
    parser = argparse.ArgumentParser(description='ACQ400 Stream AWG Multi-UUT')
    parser.add_argument('--file', required=True, type=str, help="File path, wildcard pattern, directory, or comma-separated list")
    parser.add_argument('--repeat', default=0, type=int, help='Continuous loop mode (1=enable, 0=disable)')
    parser.add_argument('--reps', default=0, type=int, help='Number of repetition loops (0=infinite if repeat enabled)')
    parser.add_argument('--soft_trigger', default=0, type=int, help='Emit soft trigger on start')
    parser.add_argument('uuts', nargs='+', help="UUT targets (e.g. uut1:54207,uut2 or uut1 uut2)")
    return parser

def run_main(args):
    files = resolve_files(args.file)
    print(f"Streaming {len(files)} file(s): {[os.path.basename(f) for f in files]}")

    uut_targets = [uut for uut_arg in args.uuts for uut in uut_arg.split(',') if uut]

    streamers = []
    repeat_flag = bool(args.repeat) or (args.reps > 0)
    
    for target in uut_targets:
        t = UUTStreamer(
            target_spec=target,
            file_list=files,
            repeat=repeat_flag,
            reps=args.reps,
            soft_trigger=args.soft_trigger
        )
        streamers.append(t)
        t.start()

    try:
        monitor(streamers)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupt received (Ctrl+C). Stopping streams...")
        for t in streamers:
            t.stop()
        sys.exit(0)

if __name__ == '__main__':
    run_main(get_parser().parse_args())
