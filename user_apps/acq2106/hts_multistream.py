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
                          [--delete DELETE] [--recycle RECYCLE] [--check CHECK]
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
  --check               run tests on data
  
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
    parser.add_argument('--check', default=0, type=int, help='check simulate ramp=1 or check spad sequential=2')

    parser.add_argument('uutnames', nargs='+', help="uuts")
    return parser

## "world" data structure is indexed by name, and is a mapping of:
## 'API' :: uut proxy object
## 'UID' :: [ uut_serial uutname ]
## 'PRT':: port map
## 'SRM' :: stream info
## 'STA' :: status


def run_main(args):
    args.map = map_parser_and_validator(args.map)
    args.world = build_data_structure(args.uutnames, args.map)
    get_ramdisk_ready(args.world, args)
    setup_remote_sites(args.world, args)
    configure_shot(args.world, args)
    run(args.world, args)

def map_parser_and_validator(maps):
    valid_remote_ports = ['A', 'B', 'BOTH']
    maps = maps.split('/')
    port_map = {}
    for map in maps:
        uutname, port, sites = map.upper().split(':')
        uutname = uutname.lstrip('0')
        if port not in valid_remote_ports:
            exit(PR.Red(f'ERROR: Invalid port: {port}'))
        if uutname not in port_map:
            port_map[uutname] = {}
        if port == 'BOTH':
            port_map[uutname]['A'] = sites
            port_map[uutname]['B'] = sites
            continue
        port_map[uutname][port] = sites
    return port_map

def build_data_structure(uutnames, map):
    world = {}
    stream_conns = get_stream_idents()
    for uut in uutnames:
        new_obj = {}
        new_obj['API'] = attach_hapi(uut)
        uid = get_uid(new_obj)
        new_obj['UID'] = uid
        
        if 'ALL' in map:
            new_obj['PRT'] = map['ALL']
        elif uid[0] in map:
            new_obj['PRT'] = map[uid[0]]
        else:
            PR.Red(f'Warning: UUT {uut} has no port map')

        new_obj['SRM'] = attach_stream(uid[1], stream_conns)
        if not new_obj['SRM']:
            del new_obj
            PR.Red(f'Warning: {uut} has no connections ignoring')
            continue

        new_obj['STA'] = {
            'last_poll'     : 0,
            'poll_delay'    : 2,
            'state'         : None,
        }

        world[uut] = new_obj
    if not world:
        exit(PR.Red("Error: No valid connections detected exiting"))
    return world

def get_ramdisk_ready(uuts, args):

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
        PR.Blue(f'Memory needed: {memory_needed} MB')
        PR.Blue(f'Memory available: {free_memory} MB')
        if memory_needed > free_memory - 1024:
            exit(PR.Red(f'Error: Needed memory exceeds safe usage'))

def get_uid(uut_item):
    uut = uut_item['API']
    hostname = uut.s0.HN
    match = re.search(r'^acq[\d]+_([\d]+)$', hostname)
    if not match:
        exit(PR.Red(f'Error: {uut_item} Hostname {hostname} is invalid'))
    return [match.group(1).lstrip('0'), match.group()]

def attach_hapi(uut_name):
    try:
        uut = acq400_hapi.factory(uut_name)
    except Exception:
        exit(PR.Red(f'Error: Connection failed {uut_name}'))
    return uut

def attach_stream(uut_name, stream_conns):
    if uut_name in stream_conns:
        return stream_conns[uut_name]
    return None

def read_knob(knob):
    with open(knob, 'r') as f:
        return f.read().strip()

def get_stream_idents():
    local_ports = range(16)
    config = {}
    for lport in local_ports:
        if not os.path.exists(f'/dev/rtm-t.{lport}.ctrl/'):
            continue
        kill_stream_if_active(lport)
        remote_port = read_knob(f'/dev/rtm-t.{lport}.ctrl/acq_port')
        remote_name = read_knob(f'/dev/rtm-t.{lport}.ctrl/acq_ident')
        if remote_name not in config:
            config[remote_name] = {}
        config[remote_name][lport] = {}
        config[remote_name][lport]['rport'] = remote_port
        config[remote_name][lport]['process'] = 'uninitialized'
        config[remote_name][lport]['mapped_sites'] = 'unknown'
    return config

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
        exit(PR.Red(f'Fatal Error: Stream failed to die {lport}'))

def stream_exists(lport):
    if os.path.isdir('/dev/rtm-t.{}.ctrl'.format(lport)):
        return True
    return False

def get_stream_pid(lport):
    return int(read_knob("/dev/rtm-t.{}.ctrl/streamer_pid".format(lport)))

def get_site_data(uut):
    input_sites=['dio']
    sites = {}
    for site in uut.s0.SITELIST.split(','):
        site = site.split('=')
        if len(site) != 2:
            continue
        if site[1] in input_sites:
            continue
        site_proxy = getattr(uut, f's{site[0]}')
        sites[site[0]] = int(site_proxy.NCHAN)
    return sites

def map_sites_to_stream(rport, sites, streams):
    for stream in streams.items():
        if stream[1]['rport'] == rport:
            stream[1]['mapped_sites'] = sites

def setup_remote_sites(uut_collection, args):
    for uut_item in uut_collection.items():
        ports = uut_item[1]['PRT']
        uut =  uut_item[1]['API']
        streams = uut_item[1]['SRM']
        
        all_sites = get_site_data(uut)
        if args.spad != None:
            uut.s0.spad = args.spad
            uut.cA.spad = 1
            uut.cB.spad = 1
            for sp in ('1', '2', '3', '4' , '5', '6', '7'):
                uut.s0.sr("spad{}={}".format(sp, sp*8))
        else:
            uut.cA.spad = 0
            uut.cB.spad = 0

        if 'A' in ports:
            sites = ports['A']
            if sites == 'ALL':
                sites = all_sites
            if sites == 'SPLIT':
                sites = all_sites[:len(all_sites) - 1]
            map_sites_to_stream('A', sites, streams)
            sites = ','.join(sites.keys())
            ports['A'] = sites
            uut.cA.spad = 0 if args.spad is None else 1
            uut.cA.aggregator = f"sites={sites} on"
        else:
            uut.cA.spad = 0
            uut.cA.aggregator = "sites=none off"

        if 'B' in ports:
            sites = ports['B']
            if sites == 'ALL':
                sites = all_sites
            if sites == 'SPLIT':
                sites = all_sites[len(all_sites) - 1:]
            map_sites_to_stream('B', sites, streams)
            sites = ','.join(sites.keys())
            ports['B'] = sites
            uut.cB.spad = 0 if args.spad is None else 1
            uut.cB.aggregator = f"sites={sites} on"
        else:
            uut.cB.spad = 0
            uut.cB.aggregator = "sites=none off"
            
def configure_shot(uut_collection, args):
    for uut_item in uut_collection.items():
        uut = uut_item[1]['API']
        acq400_hapi.Acq400UI.exec_args(uut, args)
        uut.s0.run0 = f'{uut.s0.sites} {args.spad}'
        if args.decimate is not None:
            uut.s0.decimate = args.decimate
        if args.sig_gen:
            uut.s1.TRG_DX = 'd0'
        else:
            uut.s1.TRG_DX = 'd1'
            
def start_uuts(uut_collection):
    for uid in uut_collection:
        uut = uut_collection[uid]['API']
        state = get_uut_state(uut)
        if state != 'IDLE':
            #uut.s0.CONTINUOUS = '0'
            uut.s0.streamtonowhered = "stop"
            #time.sleep(5)
        #uut.s0.CONTINUOUS = '1'
        uut.s0.streamtonowhered = "start"
        PR.Yellow(f"Started {uid}")

def stop_uuts(uut_collection):
    streams = []
    for uid in uut_collection:
        uut_collection[uid]['STA']['poll_delay'] = 0
        uut = uut_collection[uid]['API']
        #uut.s0.CONTINUOUS = '0'
        uut.s0.streamtonowhered = "stop"
        #PR.Yellow(f'Stopping {uid}')
        for lport in uut_collection[uid]['SRM']:
            streams.append(lport)
    for lport in streams:    
        kill_stream_if_active(lport)

def initialize_streams(uut_collection, args):
    nbuffers = args.nbuffers
    recycle = 1
    if not args.recycle:
        recycle = 0
    for uut_item in uut_collection.items():
        for stream in uut_item[1]['SRM'].items():
            if not args.check:
                cmd = 'sudo ./scripts/run-stream-ramdisk {} {} {}'
                cmd = cmd.format(stream[0], nbuffers, recycle).split()
            elif args.check == 1:
                cmd = 'sudo ./scripts/run-stream-ramdisk-ramp {} {} {}'
                cmd = cmd.format(stream[0], nbuffers, recycle).split()
            elif args.check == 2:
                ccolumn = 0
                for site in stream[1]['mapped_sites'].items():
                    ccolumn += site[1]
                ccolumn = int(ccolumn / 2)
                spadl = int(args.spad.split(',')[1])
                cmd = 'sudo ./scripts/run-stream-ramdisk-count {} {} {} {} {} >/dev/null 2>&1 &'
                cmd = cmd.format(stream[0], nbuffers, recycle, ccolumn, spadl).split()
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time_start = time.time()
            pid = get_stream_pid(stream[0])
            while True:
                if time.time() - time_start > 5:
                    PR.Red(f"Error: afhba.{stream[0]} failed to start")
                    break
                pid = get_stream_pid(stream[0])
                if pid != 0:
                    PR.Green(f"Started afhba.{stream[0]} with PID {pid}")
                    stream[1]['process'] = process
                    stream[1]['pid'] = pid
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

def get_results(file):
    if os.path.exists(file):
        f = open(file, "r").readline().strip()
        return f

def run(uut_collection, args):
    if args.secs:
        args.nbuffers = 99999999999

    t_mins, t_secs = divmod(args.secs, 60)

    initialize_streams(uut_collection, args)
    start_uuts(uut_collection)
    
    count = 0
    cycle_max = 1
    all_running = False
    all_armed = False
    farewell_tour = False
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
                if farewell_tour: 
                    count = args.secs
                if args.secs <= 60:
                    SCRN.add("{0:.1f}/{1} secs ", count, args.secs)
                else:
                    c_mins, c_secs = divmod(count, 60)
                    SCRN.add(f"{int(c_mins)}:{int(c_secs):02}/{int(t_mins)}:{int(t_secs):02} mins ")
                SCRN.add(f"Buffer Length: {args.buffer_len}MB {{RESET}}")
            else:
                SCRN.add("{0:.0f} secs ",time.time() - time_start)
                SCRN.add("Max: {0}MB Buffer Length: {1}MB {RESET}", args.nbuffers * args.buffer_len, args.buffer_len)

            if args.sig_gen:
                if all_armed:
                    SCRN.add(f" Triggering{args.sig_gen}")
                    try:
                        acq400_hapi.Agilent33210A(args.sig_gen).trigger()
                    except Exception:
                        PR.Red(f'Could not trigger {args.sig_gen}')
                        break
                    args.sig_gen = None
                else:
                    SCRN.add(f" Waiting to trigger {args.sig_gen}")

            SCRN.add_line('')

            for uid in uut_collection.items():
                uut_name = uid[0]
                uut_item = uid[1]
                status = uut_item['STA']
                streams = uut_item['SRM']
                uut = uut_item['API']

                if time.time() - status['last_poll'] > status['poll_delay']:
                    status['last_poll'] = time.time()
                    status["state"] = get_uut_state(uut)
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

                for stream in streams:
                    total_streams += 1
                    process = streams[stream]['process']
                    rx, rx_rate, state = get_stream_state(stream, args)
                    port = streams[stream]['rport']
                    sites = uut_item["PRT"][port]
                    SCRN.add(f'{{TAB}}{sites}:{port} -> afhba.{stream}')
                    SCRN.add(f'{{TAB}}{rx_rate}MB/s Total: {rx}MB Status: {state}')
                    if args.check == 1:
                        file = f"/mnt/afhba.{stream}/ramp_{stream}.log"
                        SCRN.add(' {0}', get_results(file))
                    if args.check == 2:
                        file = f"/mnt/afhba.{stream}/count_{stream}.log"
                        SCRN.add(' {0}', get_results(file))
                    SCRN.end()

                    if state == 'STOP_DONE':
                        status['poll_delay'] = 10
                        ended_streams += 1

                SCRN.add_line('')

            if running_uuts == len(uut_collection):
                all_running = True
            if armed_uut == len(uut_collection):
                all_armed = True

            if count and time.time() - time_start > args.secs:
                SCRN.add_line('{BOLD}Time Limit Reached Stopping{RESET}')
                if farewell_tour:
                    SCRN.render(False)
                    break
                stop_uuts(uut_collection)
                farewell_tour = True

            if ended_streams == total_streams:
                SCRN.add_line('{BOLD}Buffer limit Reached Stopping{RESET}')
                if farewell_tour:
                    SCRN.render(False)
                    break
                stop_uuts(uut_collection)
                farewell_tour = True

            cycle_length = time.time() - cycle_start
            sleep_time = 0 if cycle_length > cycle_max else cycle_max - cycle_length
            
            SCRN.render()

            time.sleep(sleep_time)

    except KeyboardInterrupt:
        SCRN.render_interrupted()
        PR.Red('Interrupt!')
        stop_uuts(uut_collection)
    except Exception:
        SCRN.render_interrupted()
        PR.Red('ERROR!')
        stop_uuts(uut_collection)
    print('Done')


# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())
