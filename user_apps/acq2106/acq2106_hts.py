#!/usr/bin/env python

""" acq2106_hts High Throughput Streaming

    - data on local SFP/AFHBA
    - control on Ethernet
    - replaces AFHBA404/scripts/hts-test-harness-*

example usage::

	./acq2106_hts.py --trg=notouch --secs=3600 acq2106_061
	    # act on acq2106_061, run for 3600s


usage::

     acq2106_hts.py [-h] [--pre PRE] [--clk CLK] [--trg TRG] [--sim SIM]
                      [--trace TRACE] [--post POST] [--secs SECS]
                      [--spad SPAD] [--commsA COMMSA] [--commsB COMMSB]
                      [--decimate DEC]
                      uut [uut ...]

configure acq2106 High Throughput Stream

positional arguments:
  uut              uut

optional arguments:
  -h, --help       show this help message and exit
  --pre PRE        pre-trigger samples
  --clk CLK        int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG        int|ext,rising|falling
  --sim SIM        s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE    1 : enable command tracing
  --post POST      capture samples [default:0 inifinity]
  --secs SECS      capture seconds [default:0 inifinity]
  --spad SPAD      scratchpad, eg 1,16,0
  --commsA COMMSA  custom list of sites for commsA
  --commsB COMMSB  custom list of sites for commsB
  --hexdump        hexdump command string
  --decimate DECIMATE  decimate arm data path

"""

import sys
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse
import time
import os


def config_shot(uut, args):
    acq400_hapi.Acq400UI.exec_args(uut, args)
    uut.s0.run0 = uut.s0.sites
    if args.decimate != None:
        uut.s0.decimate = args.decimate

def hexdump_string(uut, chan, sites, spad):
    nspad = 0 if spad == None else int(spad.split(',')[1])
    print("hexdump_string {} {} {}".format(chan, sites, nspad))
    dumpstr = ("hexdump -ve '\"%10_ad,\" ")
    for svc in ( uut.svc['s{}'.format(s)] for s in sites.split(',')):
        d32 = svc.data32 == '1'
	fmt = '" " {}/{} "%0{}x," '.format(svc.NCHAN, 4 if d32 else 2, 8 if d32 else 4)
	dumpstr += fmt
    if nspad:
        fmt = '{}/4 "%08x," '.format(nspad)
        dumpstr += fmt
    dumpstr += '"\\n"\''
    print(dumpstr)
    with open("hexdump{}".format(chan), "w") as fp:
        fp.write("{} $*\n".format(dumpstr))
    os.chmod("hexdump{}".format(chan), 0777)

def init_comms(uut, args):
    if args.spad != None:
        uut.s0.spad = args.spad
        # use spare spad elements as data markers
        for sp in ('1', '2', '3', '4' , '5', '6', '7'):
            uut.s0.sr("spad{}={}".format(sp, sp*8))
    if args.commsA != "none":
        uut.cA.spad = 0 if args.spad == None else 1
        csites = uut.s0.sites if args.commsA == 'all' else args.commsA
        uut.cA.aggregator = "sites=%s" % (csites)
        if args.hexdump:
            hexdump_string(uut, "A", csites, args.spad)
    if args.commsB != "none":
        uut.cB.spad = 0 if args.spad == None else 1
        csites = uut.s0.sites if args.commsB == 'all' else args.commsB
        uut.cB.aggregator = "sites=%s" % (csites)
        if args.hexdump:
            hexdump_string(uut, "B", csites, args.spad)

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
    acq400_hapi.Acq400UI.add_args(parser, post=False)
    parser.add_argument('--post', default=0, help="capture samples [default:0 inifinity]")
    parser.add_argument('--secs', default=999999, help="capture seconds [default:0 inifinity]")
    parser.add_argument('--spad', default=None, help="scratchpad, eg 1,16,0")
    parser.add_argument('--commsA', default="all", help='custom list of sites for commsA')
    parser.add_argument('--commsB', default="none", help='custom list of sites for commsB')
    parser.add_argument('--hexdump', default=0, help="generate hexdump format string")
    parser.add_argument('--decimate', default=None, help='decimate arm data path')
    parser.add_argument('uut', nargs='+', help="uut ")
    run_shot(parser.parse_args())



# execution starts here

if __name__ == '__main__':
    run_main()

