#!/usr/bin/env python

""" acq2106_hts
    control High Throughput Streaming on local SFP/AFHBA
    replaces AFHBA404/scripts/hts-test-harness-*
"""

import sys
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse
import time


def config_shot(uut, args):
    acq400_hapi.Acq400UI.exec_args(uut, args) 
    uut.s0.run0 = uut.s0.sites


def init_comms(uut, args):
    if args.spad != None:
        uut.s0.spad = args.spad
        # use spare spad elements as data markers
        for sp in ('1', '2', '3', '4' , '5', '6', '7'):
            uut.s0.sr("spad{}={}".format(sp, sp*8))
    if args.commsA != "none":
        uut.cA.spad = 0 if args.spad == None else 1
        uut.cA.aggregator = "sites=%s" % (uut.s0.sites if args.commsA == 'all' else args.commsA)
    if args.commsB != "none":
        uut.cB.spad = 0 if args.spad == None else 1
        uut.cB.aggregator = "sites=%s" % (uut.s0.sites if args.commsB == 'all' else args.commsB)

def init_work(uut, args):
    print "init_work"

def start_shot(uut, args):    
    uut.s0.streamtonowhered = "start"


def stop_shot(uut):
    print("stop_shot")
    uut.s0.streamtonowhered = "stop"

def run_shot(args):    
    uut = acq400_hapi.Acq2106(args.uut[0])

    config_shot(uut, args)
    init_comms(uut, args)
    init_work(uut, args)
    try:
        start_shot(uut, args)
        for ts in range(0, int(args.secs)):
            sys.stdout.write("Time ... %8d / %8d\r" % (ts, int(args.secs)))
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    stop_shot(uut)



def run_main():    
    parser = argparse.ArgumentParser(description='configure acq2106 High Throughput Stream')    
    acq400_hapi.Acq400UI.add_args(parser)
    parser.add_argument('--post', default=0, help="capture samples [default:0 inifinity]")
    parser.add_argument('--secs', default=999999, help="capture seconds [default:0 inifinity]")
    parser.add_argument('--spad', default=None, help="scratchpad, eg 1,16,0")
    parser.add_argument('--commsA', default="all", help='custom list of sites for commsA')
    parser.add_argument('--commsB', default="none", help='custom list of sites for commsB')
    parser.add_argument('uut', nargs='+', help="uut ")
    run_shot(parser.parse_args())



# execution starts here

if __name__ == '__main__':
    run_main()

