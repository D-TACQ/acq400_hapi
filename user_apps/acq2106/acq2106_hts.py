#!/usr/bin/env python3

""" acq2106_hts High Throughput Streaming

    - data on local SFP/AFHBA
    - control on Ethernet
    - replaces AFHBA404/scripts/hts-test-harness-*

example usage::
    ./user_apps/acq2106/acq2106_hts.py --map=133:A:1/133:B:2 --nbuffers=1000 acq2106_133

    ./user_apps/acq2106/acq2106_hts.py --map=67:BOTH:ALL --secs=30 acq2106_067

    ./user_apps/acq2106/acq2106_hts.py --map=1:A:ALL/2:BOTH:3,4 --lports-0,4,8,12 --nbuffers=1000 192.168.1.1 192.168.1.2



usage::
    acq2106_hts.py [-h] [--pre PRE] [--clk CLK] [--trg TRG] [--sim SIM]
                      [--trace TRACE] [--nowait NOWAIT] [--secs SECS]
                      [--spad SPAD] [--lports LPORTS] [--hexdump HEXDUMP]
                      [--decimate DECIMATE] [--map MAP]
                      [--nbuffers NBUFFERS] [--sig_gen SIG_GEN]
                      uut [uut ...]

configure acq2106 High Throughput Stream

positional arguments:
  uuts                  uuts

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
  --lports LPORTS       local ports on ahfba overrides auto detection
  --hexdump HEXDUMP     generate hexdump format string
  --decimate DECIMATE   decimate arm data path
  --nbuffers NBUFFERS   set capture length in buffers
  --map MAP             uut port configuration see below
  --sig_gen SIG_GEN     signal gen to send trigger when all uuts are in arm

--secs     : maximum run time for acq2106_hts, only starts counting once data is flowing
--nbuffers : data handler will stream max this number of buffers (1MB or 4MB)

acq2106_hts.py will quit on the first of either elapsed_seconds > secs or buffers == nbuffers

Recommendation: --secs is really a timeout, use --nbuffers for exact data length

--map= uut:port:sites
    ex.
        ALL:BOTH:ALL
        067:A:1,2
        067:B:2
        130:A:1,2
        999:BOTH:3,4

--map=67:A:1/67:B:2/130:BOTH:ALL
"""

from acq400_hapi import PR
import acq400_hapi
from acq400_hapi import intSI as intSI
import argparse
import time
import os
import re
import subprocess

from acq400_hapi import propellor as P

def run_main(args):    
    uuts = uut_instantiator(get_ports(args.map),get_uut(args.uut))
    num_streams = build_streams(uuts,args)
    config_shot(uuts, args)
    init_comms(uuts,args)
    start_shot(uuts)
    if args.nowait == 0:
        wait_completion(uuts,num_streams,args)

def build_streams(uuts,args):
    valid_ports = [0,4,8,12]
    streams = 0
    if args.lports:
        ruut = list(uuts.keys())[0]
        args.lports = args.lports.split(',')
        for lport in args.lports:
            attach_stream(uuts[ruut],lport,args)
            streams += 1
        return streams

    for lport in valid_ports:
        if not os.path.isdir('/dev/rtm-t.{}.ctrl'.format(lport)):
            continue
        kill_stream(lport)
        ruut, rport = get_conn(lport)
        if ruut in uuts:
            if rport in uuts[ruut]['ports']:
                attach_stream(uuts[ruut],lport,args)
                streams += 1
            elif 'BOTH' in uuts[ruut]['ports']:
                attach_stream(uuts[ruut],lport,args)
                streams += 1
    return streams

def get_conn(lport):
    rport = read_knob('/dev/rtm-t.{}.ctrl/acq_port'.format(lport))
    ruut = read_knob('/dev/rtm-t.{}.ctrl/acq_ident'.format(lport))
    return ruut, rport
    
def attach_stream(uut,lport,args):
    nbuffers = args.nbuffers
    cmd = 'sudo ./scripts/run-stream-ramdisk {} {}'
    cmd = cmd.format(lport, nbuffers).split()
    process = subprocess.Popen(cmd,stdout = subprocess.PIPE,stderr = subprocess.PIPE,universal_newlines=True)
    start = time.time()
    while True:
        if time.time() - start > 5:
            exit("Error: Stream failed to start")
        pid = get_data_pid(lport)
        if pid != 0:
            print("Stream {} started with PID {}".format(lport,pid))
            uut['streams'][lport] = process
            return
        time.sleep(0.1)

def get_ports(maps):
    maps = maps.split("/")
    output = {}
    for port in maps:
        port = port.upper()
        port = port.split(':')
        if port[0] in output:
            output[port[0]][port[1]] = port[2]
        else:
            output[port[0]] = {}
            output[port[0]][port[1]] = port[2]
    return output

def get_uut(uuts):
    output = {}
    for uut in uuts:
        match = re.search(r'acq[\d]+_([\d]+)', uut)
        if not match:
            print('INFO: Non-standard uut Found: {} using positional arguments instead'.format(uut))
            output = {}
            for i, uut in enumerate(uuts):
                output[str(i + 1)] = uut
            return output 
        output[match.group(1).lstrip('0')] = match.group()
    return output

def uut_instantiator(ports,uuts):
    output = {}
    if 'ALL' in ports:
        for uut in uuts:
            output[uuts[uut]] = {}
            output[uuts[uut]]['ports'] = ports[uut]
            output[uuts[uut]]['hapi'] = acq400_hapi.factory(uuts[uut])
            output[uuts[uut]]['streams'] = {}
        return output   
    for uut in uuts:
        if uut not in ports:
            exit("Error: uut portmap mismatch")
        output[uuts[uut]] = {}
        output[uuts[uut]]['ports'] = ports[uut]
        output[uuts[uut]]['hapi'] = acq400_hapi.factory(uuts[uut])
        output[uuts[uut]]['streams'] = {}
    return output

def get_data_pid(lport):
    return int(read_knob("/dev/rtm-t.{}.ctrl/streamer_pid".format(lport)))

def kill_stream(lport):
    pid = get_data_pid(lport)
    if pid == 0 or pid == 'ERROR':
        return
    cmd = 'sudo kill -9 {}'.format(pid)
    result = os.system(cmd)
    PR.Yellow('Killing stream with pid: {}'.format(pid))
    time.sleep(3)
    if result != 0:
       exit(PR.Red('FAILED TO KILL'))

def get_streamers_state(streamers):
    for streamer in streamers:
        job = read_knob("/proc/driver/afhba/afhba.{}/Job".format(streamer))
        for pp in job.split():
            k, v = pp.split('=')
            streamers[streamer][k] = v
    return streamers

def config_shot(uuts, args):
    for uid in uuts:
        uut = uuts[uid]['hapi']
        acq400_hapi.Acq400UI.exec_args(uut, args)
        uut.s0.run0 = "{} {}".format(uut.s0.sites, args.spad)
        if args.decimate != None:
            uut.s0.decimate = args.decimate
        if args.sig_gen != None:
            uut.s1.TRG_DX = 'd0'

def read_knob(knob):
    if not os.path.isfile(knob):
        return 'ERROR'
    with open(knob, 'r') as f:
        return f.read().strip()

def init_comms(uuts, args):
    for uid in uuts:
        uut = uuts[uid]['hapi']
        ports = uuts[uid]['ports']
        if args.spad != None:
            uut.s0.spad = args.spad
            # use spare spad elements as data markers
            for sp in ('1', '2', '3', '4' , '5', '6', '7'):
                uut.s0.sr("spad{}={}".format(sp, sp*8))

        if 'BOTH' in ports:
            sites = ports['BOTH']
            if sites == 'ALL':
                sites = uut.s0.sites
            uut.cA.aggregator = "sites={} on".format(sites)
            time.sleep(1)
            uut.cB.aggregator = "sites={} on".format(sites)
            if args.hexdump:
                hexdump_string(uut, "AB", sites, args.spad) 
            continue

        if 'A' in ports:
            sites = ports['A']
            if sites == 'ALL':
                sites = uut.s0.sites
            uut.cA.spad = 0 if args.spad == None else 1
            uut.cA.aggregator = "sites={} on".format(sites)
            if args.hexdump:
                hexdump_string(uut, "A", sites, args.spad)
        else:
            uut.cA.spad = 0
            uut.cA.aggregator = "sites=none off"

        if 'B' in ports:
            sites = ports['B']
            if sites == 'ALL':
                sites = uut.s0.sites
            uut.cB.spad = 0 if args.spad == None else 1
            uut.cB.aggregator = "sites={} on".format(sites)
            if args.hexdump:
                hexdump_string(uut, "B", sites, args.spad)            
        else:
            uut.cB.spad = 0
            uut.cB.aggregator = "sites=none off"

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

def start_shot(uuts):
    for uid in uuts:
        uut = uuts[uid]['hapi']
        state = get_uut_state(uut)
        if state != 'IDLE':
            PR.Yellow("Stopping uut")
            uut.s0.streamtonowhered = "stop"
            #uut.s0.CONTINUOUS = "stop"
            time.sleep(1)
        print()
        PR.Yellow(uid)
        print("\t PORTS: ",uuts[uid]['ports'])
        print("\t STREAMS:",*uuts[uid]['streams'])
        uut.s0.streamtonowhered = "start"
        #uut.s0.CONTINUOUS = "start"

def get_uut_state(uut):
    return uut.s0.CONTINUOUS_STATE.split(' ')[1]

def get_stream_state(sid):
    arr = {}
    job = read_knob("/proc/driver/afhba/afhba.{}/Job".format(sid))
    for pp in job.split():
        k, v = pp.split('=')
        arr[k] = v
    return arr

def stop_shot(uuts):
    print('Cleanup')
    for uid in uuts:
        PR.Yellow('Stopping {}'.format(uid))
        uuts[uid]['hapi'].s0.streamtonowhered = "stop"
        time.sleep(2)
        for stream in uuts[uid]['streams']:
            kill_stream(stream)
    PR.Green("DONE")

def wait_completion(uuts,num_streams,args):
    LINE_UP = '\033[1A'
    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'
    LINE_CLEAR = '\x1b[2K'
    print(HIDE_CURSOR)

    num_lines = len(uuts) + num_streams + 2
    time_start = time.time()
    trigger = ''
    ready = False
    x = True
    count = 0
    try:
        while True:
            ready_uuts = 0
            ended_streams = 0
            
            if args.secs and ready:
                if count == 0:
                    print(LINE_CLEAR,end='')
                    time_start = time.time()
                if count >= int(args.secs):
                    print('{} secs elapsed'.format(args.secs),end='')
                    print('\n' * (num_lines - 1))
                    break
                count = time.time() - time_start 
                print('{:.2f}/{} secs'.format(count,args.secs),end='')
            else:
                print('{:.2f} secs nbuffers: {}'.format(time.time() - time_start,args.nbuffers),end='')

            if args.sig_gen and ready:
                print("Triggering {}".format(args.sig_gen),end='')
                acq400_hapi.Agilent33210A(args.sig_gen).trigger()
                args.sig_gen = None
            print()

            for uid in uuts:
                uut = uuts[uid]
                state = get_uut_state(uut['hapi'])
                print('{} Status: {} '.format(uid,state))
                if state == 'RUN' or state == 'ARM':
                    ready_uuts += 1
                for stream in uut['streams']:
                    state = get_stream_state(stream)
                    print(LINE_CLEAR,end='')
                    print('Stream {} rx: {} rx_rate: {} status: {}'.format(stream,state['rx'],state['rx_rate'],state['STATUS']))
                    if state['STATUS'] == 'STOP_DONE':
                        ended_streams += 1
            
            if ended_streams == num_streams:
                break
            
            if ready_uuts == len(uuts):
                ready = True

            time.sleep(0.3)
            print(LINE_UP * num_lines)

    except KeyboardInterrupt:
        pass
    print(SHOW_CURSOR)
    stop_shot(uuts)

def get_parser():    
    parser = argparse.ArgumentParser(description='configure acq2106 High Throughput Stream')    
    acq400_hapi.Acq400UI.add_args(parser, transient=False)
    parser.add_argument('--nowait', default=0, help='start the shot but do not wait for completion')
    parser.add_argument('--secs', default=0, help="capture seconds [default:0 inifinity]")
    parser.add_argument('--spad', default=None, help="scratchpad, eg 1,16,0")
    parser.add_argument('--hexdump', default=0, help="generate hexdump format string")
    parser.add_argument('--decimate', default=None, help='decimate arm data path')
    parser.add_argument('--nbuffers', type=int, default=5000, help='set capture length in buffers')
    parser.add_argument('--etrig', type=int, default=0, help='ext trigger TODO')

    parser.add_argument('--map', default="ALL:BOTH:ALL", help='uut:port:site ie --map=67:A:1/67:B:2/130:BOTH:ALL or 1:A:1/1:B:2/2:BOTH:ALL')
    parser.add_argument('--sig_gen', default=None, help='Signal gen to trigger when everything ready')
    parser.add_argument('--lports', default=None, help='Override auto port')

    parser.add_argument('uut', nargs='+', help="uuts")
    return parser

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())

