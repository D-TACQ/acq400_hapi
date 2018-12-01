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
                      [--trace TRACE] [--nowait NOWAIT] [--secs SECS]
                      [--spad SPAD] [--commsA COMMSA] [--commsB COMMSB]
                      [--lport LPORT] [--hexdump HEXDUMP]
                      [--decimate DECIMATE] [--datahandler DATAHANDLER]
                      [--nbuffers NBUFFERS]
                      uut [uut ...]

configure acq2106 High Throughput Stream

positional arguments:
  uut                   uut

optional arguments:
  -h, --help            show this help message and exit
  --pre PRE             pre-trigger samples
  --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG             int|ext,rising|falling
  --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE         1 : enable command tracing
  --nowait NOWAIT       start the shot but do not wait for completion
  --secs SECS           capture seconds [default:0 inifinity]
  --spad SPAD           scratchpad, eg 1,16,0
  --commsA COMMSA       custom list of sites for commsA
  --commsB COMMSB       custom list of sites for commsB
  --lport LPORT         local port on ahfba
  --hexdump HEXDUMP     generate hexdump format string
  --decimate DECIMATE   decimate arm data path
  --datahandler DATAHANDLER
                        program to stream the data
  --nbuffers NBUFFERS   set capture length in buffers

--secs     : maximum run time for acq2106_hts, only starts counting once data is flowing
--nbuffers : data handler will stream max this number of buffers (1MB or 4MB)

acq2106_hts.py will quit on the first of either elapsed_seconds > secs or buffers == nbuffers

Recommendation: --secs is really a timeout, use --nbuffers for exact data length

"""

import sys
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse
import time
import os
import signal

from propellor import Propellor as P

def read_knob(knob):
    with open(knob, 'r') as f:
        return f.read()

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
    os.chmod("hexdump{}".format(chan), 0o777)

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
    print("init_work")

def get_data_pid(args):
    return int(read_knob("/dev/rtm-t.{}.ctrl/streamer_pid".format(args.lport)))

def start_shot(uut, args):    
    uut.s0.streamtonowhered = "start"


def stop_shot(uut, args):
    print("stop_shot")
    uut.s0.streamtonowhered = "stop"
    time.sleep(1)
    pid = get_data_pid(args)
    if pid != 0:
        os.system('sudo kill -9 {}'.format(pid))


def get_state(args):
    job = read_knob("/proc/driver/afhba/afhba.{}/Job".format(args.lport))
    env = {}
    for pp in job.split():
        k, v = pp.split('=')
        env[k] = v
    args.job_state = env


def wait_completion(uut, args):
    ts  = 0
    STATFMT = "Rate %d NBUFS %d Time ... %8d / %8d %s"
    try:
        while ts < int(args.secs):
            get_state(args)
            buf_rate = int(args.job_state['rx_rate'])
            rx = int(args.job_state['rx'])
            if args.datahandler != None:
                pid = get_data_pid(args)
                if pid == 0:
                    print("\ndatahandler has dropped out at NBUFS {}/{} {}".format(
                        rx, args.nbuffers, "COMPLETE" if rx>=args.nbuffers else "ERROR" ))
                    break
            sys.stdout.write( (STATFMT+"\r") % (buf_rate, rx, ts, int(args.secs), P.spin()))
            sys.stdout.flush()
            time.sleep(1)
            if buf_rate > 0:
                ts += 1
            else:
                if ts > 0:
                    sys.stdout.write(("\n" + STATFMT + "\n") % (buf_rate, rx, ts, int(args.secs), "STOPPED?"))
                    break

    except KeyboardInterrupt:
        pass
    stop_shot(uut, args)


def run_shot(args):    
    uut = acq400_hapi.Acq2106(args.uut[0])

    if args.datahandler != None:
        cmd = args.datahandler.format(args.lport, args.nbuffers)
        print("datahandler command {}".format(cmd))
        os.system(cmd)
        pollcat = 0
        pid = get_data_pid(args)
        while pid == 0:
            time.sleep(1)
            pollcat += 1
            if pollcat > 2:
                print("polling for datahandler active")
            pid = get_data_pid(args)
        print("datahandler pid {}".format(pid))

    config_shot(uut, args)
    init_comms(uut, args)
    init_work(uut, args)
    start_shot(uut, args)
    if args.nowait == 0:
        wait_completion(uut, args)


def run_main():    
    parser = argparse.ArgumentParser(description='configure acq2106 High Throughput Stream')    
    acq400_hapi.Acq400UI.add_args(parser, post=False)
    parser.add_argument('--nowait', default=0, help='start the shot but do not wait for completion')
    parser.add_argument('--secs', default=999999, help="capture seconds [default:0 inifinity]")
    parser.add_argument('--spad', default=None, help="scratchpad, eg 1,16,0")
    parser.add_argument('--commsA', default="all", help='custom list of sites for commsA')
    parser.add_argument('--commsB', default="none", help='custom list of sites for commsB')
    parser.add_argument('--lport', default=0, help='local port on ahfba')
    parser.add_argument('--hexdump', default=0, help="generate hexdump format string")
    parser.add_argument('--decimate', default=None, help='decimate arm data path')
    parser.add_argument('--datahandler', default=None, help='program to stream the data')
    parser.add_argument('--nbuffers', type=int, default=9999999999, help='set capture length in buffers')
    parser.add_argument('--etrig', type=int, default=0, help='ext trigger TODO')
    parser.add_argument('uut', nargs='+', help="uut ")
    run_shot(parser.parse_args())



# execution starts here

if __name__ == '__main__':
    run_main()

