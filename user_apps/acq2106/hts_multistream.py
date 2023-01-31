#!/usr/bin/env python3

""" hts_multistream High Throughput Streaming

    - data on local SFP/AFHBA
    - control on Ethernet

example usage::
    ./user_apps/acq2106/hts_multistream.py acq2106_133 acq2106_176

    ./user_apps/acq2106/hts_multistream.py --nbuffers=2000 acq2106_133 acq2106_176

    ./user_apps/acq2106/hts_multistream.py ---map=133:A:1/133:B:2 --secs=30 acq2106_133

    ./user_apps/acq2106/hts_multistream.py --map=643:A:ALL/124:BOTH:3,4 --nbuffers=1000 192.168.1.1 192.168.1.2

usage::
    usage: hts_multistream.py [-h] [--clk CLK] [--trg TRG] [--sim SIM]
                          [--trace TRACE]
                          [--auto_soft_trigger AUTO_SOFT_TRIGGER]
                          [--clear_counters] [--spad SPAD]
                          [--decimate DECIMATE] [--nbuffers NBUFFERS]
                          [--secs SECS] [--map MAP] [--sig_gen SIG_GEN]
                          [--delete DELETE] [--recycle RECYCLE]
                          uuts [uuts ...]

figure acq2106 High Throughput Stream

positional arguments:
  uuts                  uuts

optional arguments:
  -h, --help            show this help message and exit
  --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG             int|ext,rising|falling
  --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE         1 : enable command tracing
  --auto_soft_trigger AUTO_SOFT_TRIGGER
                        force soft trigger generation
  --clear_counters      clear all counters SLOW
  --spad SPAD           scratchpad, eg 1,16,0
  --decimate DECIMATE   decimate arm data path
  --nbuffers NBUFFERS   max capture in buffers
  --secs SECS           max capture in seconds
  --map MAP             uut:port:site ie --map=67:A:1/67:B:2/130:BOTH:ALL see below
  --sig_gen SIG_GEN     Signal gen to trigger when all uuts armed
  --delete DELETE       delete stale data
  --recycle RECYCLE     overwrite data

Recommendation: --secs is really a timeout, use --nbuffers for exact data length

If data rate exceeds bandwidth uut will stay in arm

--map=  uut:port:sites
    ex.
        ALL:BOTH:ALL
        ALL:BOTH:SPLIT - SPLIT must be used with BOTH ports
        067:A:1,2
        067:B:2
        130:A:1,2
        999:BOTH:3,4

--map=67:A:1/67:B:2/130:BOTH:ALL
"""

import acq400_hapi
from acq400_hapi import PR
from acq400_hapi.acq400_print import DISPLAY
import argparse
import time
import os
import re
import subprocess
import psutil

def get_parser():    
    parser = argparse.ArgumentParser(description='configure acq2106 High Throughput Stream')    
    acq400_hapi.Acq400UI.add_args(parser, transient=False)
    parser.add_argument('--spad', default=None, help="scratchpad, eg 1,16,0")
    parser.add_argument('--decimate', default=None, help='decimate arm data path')

    parser.add_argument('--nbuffers', type=int, default=5000, help='max capture in buffers')
    parser.add_argument('--secs', default=0, type=int, help="max capture in seconds")
    parser.add_argument('--map', default="ALL:BOTH:ALL", help='uut:port:site ie --map=67:A:1/67:B:2/130:BOTH:ALL ')
    parser.add_argument('--sig_gen', default=None, help='Signal gen to trigger when all uuts armed')
    parser.add_argument('--delete', default=1, type=int, help='delete stale data')
    parser.add_argument('--recycle', default=1, type=int, help='overwrite data')

    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

def run_main(args):
    args.map = map_parser_and_validator(args.map)
    args.uuts = build_data_structure(args.uuts,args.map)
    get_ramdisk_ready(args.uuts,args)
    setup_remote_sites(args.uuts,args)
    configure_shot(args.uuts,args)
    run(args.uuts,args)

def map_parser_and_validator(maps):
    valid_remote_ports = ['A', 'B', 'BOTH']
    maps = maps.split('/')
    port_map = {}
    for map in maps:
        uut,port,sites = map.upper().split(':')
        uut = uut.lstrip('0')
        if port not in valid_remote_ports:
            exit(PR.Red(f'ERROR: Invalid port: {port}'))
        if uut not in port_map:
            port_map[uut] = {}
        port_map[uut][port] = sites
    return port_map

def build_data_structure(uuts,map):
    struct = {}
    for uut in uuts:
        new = {}
        new['API'] = attach_hapi(uut)
        uid = get_uid(new)
        new['UID'] = uid
        if 'ALL' in map:
            new['PRT'] = map['ALL']
        elif uid[0] in map:
            new['PRT'] = map[uid[0]]
        else:
            PR.Red(f'Warning: UUT {uut} has no port map')
        new['SRM'] = attach_stream(uid[1])
        if not new['SRM']:
            del new
            PR.Red(f'Warning: {uut} has no connections ignoring')
            continue
        new['STA'] = {
            'last_poll'     : 0,
            'poll_delay'    : 2,
            'state'         : None,
        }
        new['SIT'] = {}
        struct[uut] = new
    return struct

def get_ramdisk_ready(uuts,args):

    if not os.path.ismount("/mnt"):
        exit(PR.Red(f'Error: /mnt is not a ramdisk'))

    if args.delete:
        cmd = 'sudo rm /mnt/afhba.* -rf'
        os.system(cmd)
        PR.Yellow(f"Erasing /mnt/afhba.*")
        time.sleep(4)

    args.buffer_len = int(read_knob('/sys/module/afhba/parameters/buffer_len'))
    args.buffer_len = int(args.buffer_len / 1024 / 1024)
    PR.Yellow(f'Using {args.buffer_len}MB buffers')

    if not args.recycle:
        if args.secs:
            exit(PR.Red(f'Error: --secs cannot be used if --recycle off'))
        PR.Yellow('Warning: recycling disabled')
        total_streams = 0
        free_memory = int(getattr(psutil.virtual_memory(), 'free')/1024/1024)
        for uid in uuts:
            total_streams += len(uuts[uid]['SRM'])
        memory_needed = total_streams * args.nbuffers
        PR.Blue(F'Memory needed: {memory_needed} MB')
        PR.Blue(F'Memory available: {int(free_memory)} MB')
        if memory_needed > free_memory - 1024:
            exit(PR.Red(f'Error: Needed memory exceeds safe usage'))

def get_uid(uut):
    hostname = uut['API'].s0.HN
    match = re.search(r'^acq[\d]+_([\d]+)$', hostname)
    if not match:
        exit(PR.Red(f'Error: {uut} HAPI Hostname {hostname} is invalid'))
    return [match.group(1).lstrip('0'), match.group()]

def attach_hapi(uut):
    try:
        hapi = acq400_hapi.factory(uut)
    except:
        exit(PR.Red(f'Error: Connection failed {uut}'))
    return hapi

def attach_stream(uut):
    local_ports = range(12)
    streams = {}
    for lport in local_ports:
        ruut, rport = get_stream_ident(lport)
        if uut == ruut:
            streams[lport] = [rport, 'uninitialized']
    return streams

def read_knob(knob):
    with open(knob, 'r') as f:
        return f.read().strip()

def get_stream_ident(lport):
    #improve
    if stream_exists(lport):
        kill_stream_if_active(lport)
        rport = read_knob('/dev/rtm-t.{}.ctrl/acq_port'.format(lport))
        ruut = read_knob('/dev/rtm-t.{}.ctrl/acq_ident'.format(lport))
        return ruut, rport
    return None, None

def kill_stream_if_active(lport):
    pid = get_stream_pid(lport)
    if pid == 0:
        return
    cmd = 'sudo kill -9 {}'.format(pid)
    result = os.system(cmd)
    PR.Yellow(f'Warning: Killing afhba.{lport} with pid: {pid}')
    time.sleep(4)
    pid = get_stream_pid(lport)
    if pid != 0:
        exit(PR.Red(f'FATAL ERROR: FAILED TO KILL STREAM {lport}'))

def stream_exists(lport):
    if os.path.isdir('/dev/rtm-t.{}.ctrl'.format(lport)):
        return True
    return False

def get_stream_pid(lport):
    return int(read_knob("/dev/rtm-t.{}.ctrl/streamer_pid".format(lport)))

def setup_remote_sites(uuts, args):
    for uut in uuts.items():
        hapi = uut[1]['API']
        ports = uut[1]['PRT']

        if args.spad != None:
            hapi.s0.spad = args.spad
            # use spare spad elements as data markers
            for sp in ('1', '2', '3', '4' , '5', '6', '7'):
                hapi.s0.sr("spad{}={}".format(sp, sp*8))

        if 'BOTH' in ports:
            sitesA = sitesB = ports['BOTH']
            if sitesA == 'ALL':
                sitesA = sitesB = hapi.s0.sites
            if sitesA == 'SPLIT':
                sitesA = sitesB = hapi.s0.sites.split(',')
                sitesA = ','.join(sitesA[:len(sitesA) - 1])
                sitesB = ','.join(sitesB[len(sitesB) - 1:])
            hapi.cA.aggregator = "sites={} on".format(sitesA)
            uut[1]['SIT']['A'] = sitesA
            time.sleep(1)
            hapi.cB.aggregator = "sites={} on".format(sitesB)
            uut[1]['SIT']['B'] = sitesB
            continue

        if 'A' in ports:
            sites = ports['A']
            if sites == 'ALL':
                sites = hapi.s0.sites
            hapi.cA.spad = 0 if args.spad == None else 1
            uut[1]['SIT']['A'] = sites
            hapi.cA.aggregator = "sites={} on".format(sites)
        else:
            hapi.cA.spad = 0
            hapi.cA.aggregator = "sites=none off"

        if 'B' in ports:
            sites = ports['B']
            if sites == 'ALL':
                sites = uut.s0.sites
            hapi.cB.spad = 0 if args.spad == None else 1
            uut[1]['SIT']['B'] = sites
            hapi.cB.aggregator = "sites={} on".format(sites)         
        else:
            hapi.cB.spad = 0
            hapi.cB.aggregator = "sites=none off"

def configure_shot(uuts, args):
    for uut in uuts.items():
        hapi = uut[1]['API']
        acq400_hapi.Acq400UI.exec_args(hapi, args)
        hapi.s0.run0 = "{} {}".format(hapi.s0.sites, args.spad)
        if args.decimate != None:
            hapi.s0.decimate = args.decimate
        if args.sig_gen:
            hapi.s1.TRG_DX = 'd0'
        else:
            hapi.s1.TRG_DX = 'd1'

def start_uuts(uuts):
    for uid in uuts:
        hapi = uuts[uid]['API']
        state = get_uut_state(hapi)
        if state != 'IDLE':
            #hapi.s0.streamtonowhered = "stop"
            hapi.s0.CONTINUOUS = '0'
            time.sleep(4)
        hapi.s0.CONTINUOUS = '1'
        #hapi.s0.streamtonowhered = "start"
        PR.Yellow(f"Started {uid}")

def stop_uuts(uuts):
    streams = []
    for uid in uuts:
        hapi = uuts[uid]['API']
        hapi.s0.CONTINUOUS = '0'
        hapi.s0.streamtonowhered = "stop"
        PR.Yellow(f'Stopping {uid}')
        for lport in uuts[uid]['SRM']:
            streams.append(lport)
    time.sleep(5)
    for lport in streams:    
        kill_stream_if_active(lport)

def initialize_streams(uuts,args):
    nbuffers = args.nbuffers
    recycle = 1
    if not args.recycle:
        recycle = 0
    for uut in uuts:
        for stream in uuts[uut]['SRM']:
            cmd = 'sudo ./scripts/run-stream-ramdisk {} {} {}'
            cmd = cmd.format(stream, nbuffers, recycle).split()
            process = subprocess.Popen(cmd,stdout = subprocess.PIPE,stderr = subprocess.PIPE)
            time_start = time.time()
            pid = get_stream_pid(stream)
            while True:
                if time.time() - time_start > 5:
                    PR.Red(f"Error: afhba.{stream} failed to start")
                    break
                pid = get_stream_pid(stream)
                if pid != 0:
                    PR.Green(f"Started afhba.{stream} with PID {pid}")
                    uuts[uut]['SRM'][stream][1] = process
                    break
                time.sleep(0.5)

def get_uut_state(uut):
    return uut.s0.CONTINUOUS_STATE.split(' ')[1]

def get_stream_state(sid, args):
    arr = {}
    job = read_knob("/proc/driver/afhba/afhba.{}/Job".format(sid))
    for pp in job.split():
        k, v = pp.split('=')
        arr[k] = v
    arr['STATUS'] = arr['STATUS'] if arr['STATUS'] else 'OK'
    return int(arr['rx']) * args.buffer_len, int(arr['rx_rate']) * args.buffer_len, arr['STATUS']

def run(uuts, args):

    if args.secs:
        args.nbuffers = 99999999999

    t_mins, t_secs = divmod(args.secs, 60)

    initialize_streams(uuts,args)
    start_uuts(uuts)

    

    count = 0
    cycle_max = 1
    all_running = False
    all_armed = False
    time_start = time.time()
    print("")
    SCRN = DISPLAY()

    try:
        while True:

            cycle_start = time.time()
            running_uuts = 0
            armed_uut = 0
            total_streams = 0
            ended_streams = 0

            SCRN.add('{REVERSE} ')
            if args.secs and all_running:
                if not count:
                    time_start = time.time()
                count = time.time() - time_start
                if args.secs <= 60:
                    SCRN.add("{0:.1f}/{1} secs ",count,args.secs)
                else:
                    c_mins, c_secs = divmod(count, 60)
                    SCRN.add(f"{int(c_mins)}.{int(c_secs):02}/{int(t_mins)}.{int(t_secs):02} mins ")
                SCRN.add("Max Buffers: {0} Buffer Length: {1}MB {RESET}",'N/A',args.buffer_len)
            else:
                SCRN.add("{0:.0f} secs ",time.time() - time_start)
                SCRN.add("Max Buffers: {0} Buffer Length: {1}MB {RESET}",args.nbuffers * args.buffer_len,args.buffer_len)


            if args.sig_gen:
                if all_armed:
                    SCRN.add(f" Triggering{args.sig_gen}")
                    try:
                        acq400_hapi.Agilent33210A(args.sig_gen).trigger()
                    except:
                        PR.Red(f'Could not trigger {args.sig_gen}')
                        break
                    args.sig_gen = None
                else:
                    SCRN.add(f" Waiting to trigger {args.sig_gen}")

            SCRN.add_line('')

            for uut in uuts.items():
                uut_name = uut[0]
                uut = uut[1]
                status = uut['STA']

                if time.time() - status['last_poll'] > status['poll_delay']:
                    status['last_poll'] = time.time()
                    status["state"] = get_uut_state(uut['API'])
                SCRN.add(f'{uut_name} ')
                if status["state"] == 'RUN':
                    running_uuts += 1
                    status['poll_delay'] = 10
                    SCRN.add(f'{{GREEN}}{status["state"]}{{RESET}}:')
                elif status["state"] == 'ARM':
                    armed_uut += 1
                    SCRN.add(f'{{ORANGE}}{status["state"]}{{RESET}}:')
                    if not args.sig_gen:
                        SCRN.add(f'{{RED}} Error{{RESET}}')
                else:
                    SCRN.add(f'{{RED}}{status["state"]}{{RESET}}:')
                SCRN.end()

                for stream in uut['SRM']:
                    total_streams += 1
                    rx, rx_rate, state = get_stream_state(stream,args)
                    port = uut["SRM"][stream][0]
                    sites = uut["SIT"][port]
                    SCRN.add(f'{{TAB}}{sites}:{port} -> afhba.{stream}')
                    SCRN.add(f'{{TAB}}{rx_rate}MB/s Total: {rx}MB Status: {state}')
                    SCRN.end()
                    if state == 'STOP_DONE':
                        status['poll_delay'] = 10
                        ended_streams += 1
                SCRN.add_line('')

            if running_uuts == len(uuts):
                all_running = True
            if armed_uut == len(uuts):
                all_armed = True


            if count and time.time() - time_start > args.secs:
                SCRN.add_line('{BOLD}Time Limit Reached{RESET}')
                SCRN.render(False)
                break

            if ended_streams == total_streams:
                SCRN.add_line('{BOLD}Buffer limit Reached{RESET}')
                SCRN.render(False)
                break


            cycle_length = time.time () - cycle_start
            sleep_time =  0  if cycle_length > cycle_max else cycle_max - cycle_length

            if sleep_time < 0.6:
                SCRN.add_line('{RED}Cycle took {0:.2f}s{RESET}',cycle_length)


            SCRN.render()

            time.sleep(sleep_time)

    except KeyboardInterrupt:
        SCRN.render_interrupted()
        PR.Red('Interrupt!')
        pass
    except:
        SCRN.render_interrupted()
        PR.Red('ERROR!')
        pass
    print()
    stop_uuts(uuts)

# execution starts here
if __name__ == '__main__':
    run_main(get_parser().parse_args())

