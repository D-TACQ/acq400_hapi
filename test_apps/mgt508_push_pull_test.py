#!/usr/bin/env python3

"""
control continuous capture, default is to toggle

.. rst-class:: hidden

    positional arguments:
    uut         uut

    optional arguments:
    
    --simulate   use simulated data and validate
    --clear_mem  zero memory before run
    --to_file    save data to timestamped files or not
    --GB=4       capture length in gigabytes
    --nruns=1    number of times to clear, fill, calculate sha1 sum 
    -h, --help   show this help message and exit
"""


import argparse
import hashlib
from pprint import pprint
import socket
import sys
import threading
import time

import acq400_hapi
from acq400_hapi import timing

CHUNK_SIZE = 4096


def configure_acq(args, acq):
    while acq400_hapi.pv(acq.s0.CONTINUOUS_STATE) != "IDLE":
        acq.s0.CONTINUOUS = 0
        print(f"WARNING: requesting {acq.uut} to stop")
        time.sleep(1)

    module_sites = acq.s0.get_knob("sites").split(",")
    for s in module_sites:
        acq[s].simulate = int(args.simulate)

    sites = None
    spad = None
    agg = acq.s0.aggregator
    for kv in agg.split(" "):
        key, value = kv.split("=")
        if key == "sites":
            sites = value
        if key == "spad":
            spad = value.split(",")[0]

    if sites is None or spad is None:
        print(f"unable to parse aggregator {agg}")
        sys.exit(1)
    acq.cA.aggregator = f"sites={sites} spad={spad} on"
    args.ssb = acq.s0.ssb


def configure_mgt(args, mgt):
    mgt.set_capture_length(args.GB * 0x400)
    mgt.s0.ssb = args.ssb


@timing
def nc_send_zeros(hostname, port=2211):
    """
    Use with send_zeros("mgt508-007", 2211)
    equivalent to `/dev/zero | nc`

    Write to port 2211
    """
    total_zero_bytes_written = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((hostname, port))
        try:
            while True:
                zero_data = bytes(CHUNK_SIZE)
                s.sendall(zero_data)
                total_zero_bytes_written += CHUNK_SIZE
            return 0
        except ConnectionResetError:  # This is the expected default behaviour
            print(
                f"MGT ended connection, {total_zero_bytes_written} zero bytes written"
            )
            return 0
        except KeyboardInterrupt:
            print("Transmission stopped!")
            return 130


def nc_read_data(host, gb_size, sha=False, to_file=False, port=2210):
    """
    Writes the data out to a file and calculates the sha1 hash of the data
    """

    bytes_to_receive = gb_size * 1073741824
    block_size = CHUNK_SIZE  # 1048576
    sha1_hash = hashlib.sha1()

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{host}_{timestamp}.dat"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        total_received = 0
        if to_file:
            with open(filename, "wb") as f:
                while total_received < bytes_to_receive:
                    data = s.recv(min(block_size, bytes_to_receive - total_received))
                    if not data:
                        break
                    f.write(data)
                    if sha:
                        sha1_hash.update(data)
                    total_received += len(data)
            print(f"\nFile received: {filename}.dat, Total bytes: {total_received}")
        else:
            while total_received < bytes_to_receive:
                data = s.recv(min(block_size, bytes_to_receive - total_received))
                if not data:
                    break
                if sha:
                    sha1_hash.update(data)
                total_received += len(data)
    return sha1_hash.hexdigest()


@timing
def clear_mem(mgt):
    result = nc_send_zeros(mgt.uut)
    return result


@timing
def read_data(args, mgt):
    gb_size = args.GB
    if args.simulate:
        sha1result = nc_read_data(
            mgt.uut, gb_size, sha=True
        )  # , demux_func=demux_data)
    else:
        sha1result = nc_read_data(mgt.uut, gb_size, sha=True)
    # print(f"Return code : {result.returncode}")
    return sha1result


def pull(mgt):
    print(f"Start pull {mgt.uut}")
    mgt.pull()


def start_pull(mgt):
    pull_thread = threading.Thread(target=pull, args=(mgt,))
    pull_thread.start()
    return pull_thread


@timing
def wait_pull_complete(pull_thread, mgt):
    pull_thread.join()
    print()
    print("Pull Complete")
    if mgt.capture_time:
        print(
            f"Capture {mgt.capture_blocks} time {mgt.capture_time:.2} sec {mgt.capture_blocks*32/mgt.capture_time:.0f} MB/s"
        )


def start_acq(acq):
    acq.s0.CONTINUOUS = "start"


def stop_acq(acq):
    acq.s0.CONTINUOUS = "stop"


def get_parser():
    parser = argparse.ArgumentParser(
        description="Controls acq2206+mgt508 deep memory system"
    )
    parser.add_argument(
        "--simulate", action="store_true", help="use simulated data and validate"
    )
    parser.add_argument(
        "--clear_mem", action="store_true", help="zero memory before run"
    )
    parser.add_argument(
        "--file", action="store_true", help="To save data to timestamped files or not"
    )
    parser.add_argument("--GB", type=int, default=4, help="capture length in gigabytes")
    parser.add_argument(
        "--nruns", type=int, default=1, help="number of times to fill, check, clear mem"
    )
    parser.add_argument("uut_pairs", nargs="+", help="acq2206,mgt508 [a,m] ..")

    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    hashed_results = []

    print(f"uut_pairs: {args.uut_pairs}")
    print("Command line arguments set:\n")
    pprint(args.__dict__)
    acqname, mgtname = args.uut_pairs[0].split(",")
    acq = acq400_hapi.factory(acqname)
    mgt = acq400_hapi.Mgt508(mgtname)

    for i in range(args.nruns):
        configure_acq(args, acq)
        configure_mgt(args, mgt)

        print(f"Run number {i+1} of {args.nruns}...")
        if args.clear_mem:
            clear_mem(mgt)

        pull_thread = start_pull(mgt)
        start_acq(acq)

        wait_pull_complete(pull_thread, mgt)
        stop_acq(acq)

        hashed_result = read_data(args, mgt)
        hashed_results.append(hashed_result)

    if len(set(hashed_results)) == 1 and args.simulate:
        print(
            f"With simulated data\nTEST PASSED! All results have same sha1 digest of {hashed_results[0]}\nTEST PASSED!"
        )
    elif len(set(hashed_results)) == len(hashed_results) and not args.simulate:
        print(
            f"With real data\nTEST PASSED! All results have different sha1 digests:\n{hashed_results}\nTEST PASSED!"
        )
    else:
        print(
            f"TEST FAILED! Results: {hashed_results}\n Simulate={args.simulate}\nTEST FAILED!"
        )
