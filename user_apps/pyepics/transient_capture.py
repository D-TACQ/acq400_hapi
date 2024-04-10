#!/usr/bin/env python
"""
run a transient capture. emulates CAPTURE!TRANSIENT.opi
"""
import argparse
import time
import epics
import supported_host
import pv_factory
import time

PRE = 0
POST = 100000


def configure_transient(args):
    args.PVF("MODE:TRANSIENT:POST").put(PRE)
    args.PVF("MODE:TRANSIENT:POST").put(POST)
    args.PVF("MODE:TRANSIENT").put(1)
    args.PVF("1:TRG:DX").put(args.soft_trigger)

def run_shot(args):
    args.PVF("MODE:TRANSIENT:SET_ARM").put(1)

def run_main(args):
    print("hello this is run_main")
    if not args.uut:
        args.uut = supported_host.self_hosted()
        if not args.uut:
            print("ERROR: suitable uut not defined")
            return 1
    pv_factory.verbose = args.verbose
    args.PVF = pv_factory.pv_factory(args.uut)
    uptime = args.PVF(f"SYS:UPTIME").get()
    if not uptime:
        print(f"ERROR: failed to connect to PV")
        return -1

    if args.sync_role:
        args.PVF("SYS:SYNC_ROLE").put(args.sync_role)
    if args.waterfall is not None:
        args.PVF(f"{args.site}:AI_WATERFALL").put(args.waterfall)

    configure_transient(args)
    run_shot(args)


def get_parser():
    parser = argparse.ArgumentParser(description='transient_capture')
    parser.add_argument('--verbose', default=None, type=int, help="make more verbose")
    parser.add_argument('--site', default=1, type=int, help="AI module site")
    parser.add_argument('--soft_trigger', default=1, help="0: fp (hard trigger) 1: soft_trigger")
    parser.add_argument('--sync_role', default=None, help='optional sync_role argument eg "master 10k"')
    parser.add_argument('--waterfall', type=int, default=None, help="set site 1 for waterfall display")
    parser.add_argument('uut', default=None, nargs='?', help="uut")
    return parser

if __name__ == '__main__':
	run_main(get_parser().parse_args())
