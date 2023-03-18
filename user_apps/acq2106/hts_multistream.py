#!/usr/bin/env python3

""" hts_multistream High Throughput Stream from up to 16 UUTS

    - data on local SFP/AFHBA
    - control on Ethernet

usage: hts_multistream.py [-h] [--clk CLK] [--trg TRG] [--sim SIM] [--trace TRACE] [--auto_soft_trigger AUTO_SOFT_TRIGGER] [--clear_counters] [--spad SPAD] [--decimate DECIMATE] [--nbuffers NBUFFERS]
                          [--secs SECS] [--map MAP] [--sig_gen SIG_GEN] [--delete DELETE] [--recycle RECYCLE] [--check CHECK] [--dry_run DRY_RUN] [--wrtd_txi WRTD_TXI] [--SIG_SRC_TRG_0 SIG_SRC_TRG_0]
                          [--SIG_SRC_TRG_1 SIG_SRC_TRG_1]
                          uutnames [uutnames ...]

positional arguments:
  uutnames              uuts

options:
  -h, --help            show this help message and exit
  --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
  --trg TRG             int|ext,rising|falling
  --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
  --trace TRACE         1 : enable command tracing
  --auto_soft_trigger AUTO_SOFT_TRIGGER force soft trigger generation
  --clear_counters      clear all counters SLOW
  --spad SPAD           scratchpad, eg 1,16,0
  --decimate DECIMATE   decimate amount
  --nbuffers NBUFFERS   max capture in buffers
  --secs SECS           max capture in seconds
  --map MAP             uut:port:site ie --map=67:A:1/67:B:2/130:BOTH:ALL
  --sig_gen SIG_GEN     Signal gen to trigger when all uuts armed
  --delete DELETE       delete stale data
  --recycle RECYCLE     overwrite data
  --check CHECK         run tests simulate ramp=1 or spad sequential=2
  --dry_run DRY_RUN     run setup but dont start streams or uuts
  --wrtd_txi WRTD_TXI   Command first box to send this trigger when all units are in ARM state
  --SIG_SRC_TRG_0 SIG_SRC_TRG_0     Set trigger d0 source
  --SIG_SRC_TRG_1 SIG_SRC_TRG_1     Set trigger d1 source

Recommendation: --secs is really a timeout, use --nbuffers for exact data length

example usage::
    ./user_apps/acq2106/hts_multistream.py acq2106_133 acq2106_176

    ./user_apps/acq2106/hts_multistream.py --nbuffers=2000 acq2106_133 acq2106_176

    ./user_apps/acq2106/hts_multistream.py ---map=133:A:1/133:B:2 --secs=30 acq2106_133

    ./user_apps/acq2106/hts_multistream.py --map=643:A:ALL/124:BOTH:3,4 --nbuffers=1000 acq2106_067

    ./user_apps/acq2106/hts_multistream.py --spad=1,8,1 --map=11:C:2 --secs=3600 --check=2 z7io_011

Warning: If data rate exceeds bandwidth uut will stay in arm

    --map=  uut:port:sites
        ex.
            ALL:BOTH:ALL
            ALL:BOTH:SPLIT - SPLIT must be used with BOTH ports
            067:A:1,2
            067:B:2
            999:BOTH:3,4
            11:C:1,2
            C is z7io exclusive
    --map=67:A:1/67:B:2/130:BOTH:ALL
"""
import acq400_hapi
from acq400_hapi import PR
from acq400_hapi.acq400_print import DISPLAY
from acq400_hapi import afhba404
import argparse
import time
import os
import re
import subprocess
import psutil
import threading

def get_parser():
    parser = argparse.ArgumentParser(description='High Throughput Stream from up to 16 UUTS')
    acq400_hapi.Acq400UI.add_args(parser, transient=False)
    parser.add_argument('--spad', default=None, help="scratchpad, eg 1,16,0")
    parser.add_argument('--decimate', default=1, help='decimate amount')
    parser.add_argument('--nbuffers', type=int, default=5000, help='max capture in buffers')
    parser.add_argument('--secs', default=0, type=int, help="max capture in seconds")
    parser.add_argument('--map', default="ALL:BOTH:ALL", help='uut:port:site ie --map=67:A:1/67:B:2/130:BOTH:ALL ')
    parser.add_argument('--sig_gen', default=None, help='Signal gen to trigger when all uuts armed')
    parser.add_argument('--delete', default=1, type=int, help='delete stale data')
    parser.add_argument('--recycle', default=1, type=int, help='overwrite data')
    parser.add_argument('--check', default=0, type=int, help='run tests simulate ramp=1 or spad sequential=2')
    parser.add_argument('--dry_run', default=0, type=int, help='run setup but dont start streams or uuts')
    parser.add_argument('--wrtd_txi', default=None, help='Command first box to send this trigger when all units are in ARM state')
    parser.add_argument('--SIG_SRC_TRG_0', default=None, help='Set trigger d0 source')
    parser.add_argument('--SIG_SRC_TRG_1', default=None, help='Set trigger d1 source')
    parser.add_argument('--RTM_TRANSLEN', default=None, help='Set rtm_translen for each uut')

    parser.add_argument('uutnames', nargs='+', help="uuts")
    return parser

class uut_class:

    def __init__(self, name, args, map, streams):
        self.name = name
        self.spad = args.spad
        self.args = args
        self.state = None
        self.thread = None
        self.ended = False
        self.__attach_api()
        self.__set_id()
        self.__data_builder(map, streams)

    def get_state(self):
        self.state =  acq400_hapi.pv(self.api.s0.CONTINUOUS_STATE)

    def get_state_forever(self):
        while True:
            self.get_state()
            time.sleep(1)

    def start(self):
        self.get_state()
        if self.state != 'IDLE':
            #self.api.s0.CONTINUOUS = '0'
            self.api.s0.streamtonowhered = "stop"
            time.sleep(2)
        #self.api.s0.CONTINUOUS = '1'
        self.api.s0.streamtonowhered = "start"

    def stop(self):
        #self.api.s0.CONTINUOUS = 0
        self.api.s0.streamtonowhered = "stop"
        return

    def initialize(self):
        for stream in self.streams:
            self.check_lane_status(stream, self.streams[stream]["rport"])
            args = {}
            args['lport'] = stream
            args['buffers'] = self.args.nbuffers
            args['recycle'] = self.args.recycle
            if not self.args.check:
                cmd = 'sudo ./scripts/run-stream-ramdisk {lport} {buffers} {recycle}'
            elif self.args.check == 1:
                cmd = 'sudo ./scripts/run-stream-ramdisk-ramp {lport} {buffers} {recycle}'
            elif self.args.check == 2:
                if not self.spad_enabled:
                    exit(PR.Red(f'Error: Cannot check spad if no spad: {self.spad}'))
                count_col = 0
                for site in self.streams[stream]['sites'].items():
                    count_col += int(site[1])
                count_col = int(count_col / 2)
                args['spad_len'] = int(self.spad.split(',')[1])
                args['count_col'] = count_col
                cmd = 'sudo ./scripts/run-stream-ramdisk-count {lport} {buffers} {recycle} {spad_len} {count_col}'
            cmd = cmd.format(**args)
            print(f"Cmd for stream:{stream} - {cmd}")
            self.streams[stream]['process'] = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time_start = time.time()
            pid = afhba404.get_stream_pid(stream)
            while True:
                if pid != 0:
                    PR.Green(f"Started afhba.{stream} with PID {pid}")
                    self.streams[stream]['pid'] = pid
                    break
                if time.time() - time_start > 5:
                    exit(PR.Red(f"Error: afhba.{stream} failed to start"))
                pid = afhba404.get_stream_pid(stream)
                time.sleep(0.5)

    def check_lane_status(self, lport, rport):
        link_state = afhba404.get_link_state(lport)
        message = f'{self.name} Link State LANE_UP={link_state.LANE_UP} RPCIE_INIT={link_state.RPCIE_INIT}'

        if link_state.LANE_UP and link_state.RPCIE_INIT:
            PR.Green(message)
            return
        PR.Yellow(message)
        comms = getattr(self.api, f'c{rport}')
        if not hasattr(comms, 'TX_DISABLE'):
            exit(PR.Red('Link down: could not fix (old firmware)'))
        retry = 0
        while retry < 3:
            PR.Yellow(f'{self.name} Link down: attempting to correct {retry}/3')
            comms.TX_DISABLE = 1
            time.sleep(0.5)
            comms.TX_DISABLE = 0
            time.sleep(0.5)
            link_state = afhba404.get_link_state(lport)
            if link_state.RPCIE_INIT:
                PR.Green(f'{self.name} Link Fixed {retry}')
                return
            retry += 1

        exit(PR.Red('Link down: could not fix'))

    def configure(self):
        if self.spad is not None:
            self.api.s0.spad = self.spad
        else:
            self.spad = self.api.s0.spad

        self.spad_enabled = True if int(self.spad.split(',')[0]) else False
        if self.spad_enabled:
            for sp in ('1', '2', '3', '4' , '5', '6', '7'):
                self.api.s0.sr("spad{}={}".format(sp, sp*8))
        self.__setup_aggregator()

        acq400_hapi.Acq400UI.exec_args(self.api, self.args)
        self.api.s0.run0 = f'{self.api.s0.sites} {self.spad}'
        self.api.s0.decimate = self.args.decimate
        if self.args.SIG_SRC_TRG_0 is not None:
            self.api.s0.SIG_SRC_TRG_0 = self.args.SIG_SRC_TRG_0
        if self.args.SIG_SRC_TRG_0 is not None:
            self.api.s0.SIG_SRC_TRG_1 = self.args.SIG_SRC_TRG_1
        if self.args.wrtd_txi is not None:
            self.api.s0.SIG_SRC_TRG_1 = 'WRTT1'
        if self.args.RTM_TRANSLEN is not None:
            self.api.s1.RTM_TRANSLEN = self.args.RTM_TRANSLEN
        PR.Yellow(f'Configuring {self.name}: rtm_translen {self.api.s1.rtm_translen} ssb {self.api.s0.ssb} {self.args.buffer_len}MB buffers')

    def __setup_aggregator(self):
        for stream in self.streams.items():
            method = f'c{stream[1]["rport"]}'
            comm_site = getattr(self.api, method)
            agg_str = f'sites={",".join(stream[1]["sites"].keys())} on'
            comm_site.aggregator = agg_str
            if self.spad_enabled:
                comm_site.spad = 1
            else:
                comm_site.spad = 0

    def get_stream_state(self, lport):
        return afhba404.get_stream_state(lport)

    def get_results(self, lport):
            tests = {
                1 : 'Simulate',
                2 : 'Spad Checker'
            }
            file = f"/mnt/afhba.{lport}/ramp_{lport}.log"
            data = None
            if os.path.exists(file):
                data = open(file, "r").readline().strip()
            return tests[self.args.check], data

    def __attach_api(self):
        try:
            self.api = acq400_hapi.factory(self.name)
        except Exception:
            exit(PR.Red(f'Error: Connection failed {self.name}'))

    def __set_id(self):
        hostname = self.api.s0.HN
        match = re.search(r'^.+_([0-9]{3})$', hostname)
        if not match:
            exit(PR.Red(f'Error: {self.name} Hostname {hostname} is invalid'))
        self.name = match.group()
        self.id = match.group(1).lstrip('0')

    def __data_builder(self, map, streams):
        if self.name not in streams:
            exit(PR.Red(f'Error: {self.name} has no connections'))

        self.streams = streams[self.name]
        self.ports = self.__get_mapped_sites(map)
        for stream in self.streams.copy():
            if self.streams[stream]['rport'] not in self.ports:
                del self.streams[stream]
                continue
            self.streams[stream]['sites'] = self.ports[self.streams[stream]['rport']]
            self.streams[stream]['all_sites'] = ','.join(self.streams[stream]['sites'].keys())

    def __get_mapped_sites(self, map):
        # pgm: we ONLY want to look at sites already in the s0 aggregator.
        #site_list = self.__get_sitelist()
        site_list = self.__get_aggregator_sitelist()
        out = {}
        if 'ALL' in map:
            map[self.id] = map['ALL'].copy()
        if self.id not in map:
            exit(PR.Red(f'Error: {self.name} has no valid map'))
        for port in map[self.id]:
            out[port] = {}
            map[self.id][port] = map[self.id][port].split(',')

            if map[self.id][port][0] == 'ALL':
                out[port] = site_list
                continue
            if map[self.id][port][0] == 'SPLIT':
                out['A'] = dict(list(site_list.items())[len(site_list)//2:])
                out['B'] = dict(list(site_list.items())[:len(site_list)//2])
                break
            for key in map[self.id][port]:
                if key in site_list:
                    out[port][key] = site_list[key]
            if not out[port]:
                exit(PR.Red(f'Error: {self.name} has no valid sites'))
        return out

    def __get_aggregator_sitelist(self):
        sites = {}
        for site in self.api.get_aggregator_sites():
            site_conn = getattr(self.api, f's{site}')
            sites[str(site)] = site_conn.active_chan
        return sites
    def __get_sitelist(self):
        sites = {}
        for site in self.api.get_site_types()['AISITES']:
            site_conn = getattr(self.api, f's{site}')
            sites[str(site)] = site_conn.NCHAN               # not strictly correct. Should be active_chan
        return sites

def stop_uuts(uut_collection):
    for uut_item in uut_collection:
        if not uut_item.ended:
            t = threading.Thread(target=uut_item.stop)
            t.start()
            uut_item.ended = True

def object_builder(args):
    stream_config = get_stream_conns(args)
    map = get_parsed_map(args.map)
    uut_collection = []
    for uut_name in args.uutnames:
        new_uut = uut_class(uut_name, args, map, stream_config)
        uut_collection.append(new_uut)
    return uut_collection

def get_stream_conns(args):
    config = {}
    active_conns = afhba404.get_connections()
    for conn in active_conns:
        lport = active_conns[conn].dev
        rport = active_conns[conn].cx
        rhost = active_conns[conn].uut
        kill_stream_if_active(lport)
        if rhost not in config:
            config[rhost] = {}
        config[rhost][lport] = {}
        config[rhost][lport]['rport'] = rport
    return config

def get_parsed_map(maps):
    valid_ports = ['A', 'B', 'C', 'BOTH']
    maps = maps.split('/')
    port_map = {}
    for map in maps:
        uutname, port, sites = map.upper().split(':')
        uutname = uutname.lstrip('0')
        if port not in valid_ports:
            exit(PR.Red(f'ERROR: Invalid port: {port}'))
        if uutname not in port_map:
            port_map[uutname] = {}
        if port == 'BOTH':
            port_map[uutname]['A'] = sites
            port_map[uutname]['B'] = sites
            port_map[uutname]['C'] = sites
            continue
        port_map[uutname][port] = sites
    return port_map

def kill_stream_if_active(lport):
    pid = afhba404.get_stream_pid(lport)
    if pid == 0:
        return
    cmd = 'sudo kill -9 {}'.format(pid)
    result = os.system(cmd)
    PR.Yellow(f'Warning: Killing afhba.{lport} with pid: {pid}')
    time.sleep(4)
    pid = afhba404.get_stream_pid(lport)
    if pid != 0:
        exit(PR.Red(f'Fatal Error: Stream failed to die {lport}'))

def read_knob(knob):
    with open(knob, 'r') as f:
        return f.read().strip()

def configure_host(uut_collection, args):
    if not os.path.ismount("/mnt"):
        exit(PR.Red(f'Error: /mnt is not a ramdisk'))

    if args.delete:
        cmd = 'sudo rm /mnt/afhba.* -rf'
        os.system(cmd)
        PR.Yellow(f"Erasing /mnt/afhba.*")
        time.sleep(4)

    lport = list(uut_collection[0].streams.keys())[0]
    args.buffer_len = int(afhba404.get_buffer_len(lport) / 1024 / 1024)

    if not args.recycle:
        if args.secs:
            exit(PR.Red(f'Error: --secs cannot be used if --recycle off'))
        PR.Yellow('Warning: recycling disabled')
        total_streams = 0
        free_memory = int(getattr(psutil.virtual_memory(), 'free')/1024/1024)
        for uut_item in uut_collection:
            total_streams += len(uut_item.streams)
        memory_needed = total_streams * args.nbuffers
        PR.Blue(f'Memory needed: {memory_needed} MB')
        PR.Blue(f'Memory available: {free_memory} MB')
        if memory_needed > free_memory - 1024:
            exit(PR.Red(f'Error: Needed memory exceeds safe usage'))
    if args.secs:
        args.t_mins, args.t_secs = divmod(args.secs, 60)
        args.nbuffers = 9999999999



def release_trigger_when_ready_wrapper(SCRN, args, uut_collection):
    trigg_msg = ''    
    def release_trigger_when_ready(all_armed):
        top_uut = uut_collection[0].api
        global trigg_msg
        rc = 0
        if args.sig_gen is not None:
            trigg_msg = f"Waiting to trigger {args.sig_gen}"
            if all_armed:
                try:
                    acq400_hapi.Agilent33210A(args.sig_gen).trigger()
                except Exception:
                    trigg_msg = f'{{RED}}Could not trigger {args.sig_gen}'
                    rc = -1
                trigg_msg = f'Triggered {{GREEN}}{args.sig_gen}'
                args.sig_gen = None
    
        if args.wrtd_txi:
            trigg_msg = f"Waiting to trigger wrtd_txi"
            if all_armed:
                trigg_msg = f'Triggered wrtd_txi'
                top_uut.cC.sr(args.wrtd_txi)
                args.wrtd_txi = None
    
        SCRN.add(f'{trigg_msg} {{RESET}}')
        SCRN.add_line('')
        return rc
    return release_trigger_when_ready   
  
  
def hot_run_init(uut_collection):
    total_streams = 0
    for uut_item in uut_collection:
        uut_item.configure()
        uut_item.initialize()
        total_streams += len(uut_item.streams)
    for uut_item in uut_collection:
        uut_item.thread =  threading.Thread(target=uut_item.get_state_forever)
        uut_item.thread.daemon = True
        uut_item.thread.start()
        uut_item.start()
    return total_streams

def hot_run_status_update_wrapper(SCRN, args, uut_collection):
    def hot_run_status_update():
        armed_uuts = 0
        running_uuts = 0    
        ended_streams = 0
            
        for uut_item in uut_collection:
            SCRN.add(f'{uut_item.name} ')
            if uut_item.state == 'RUN':
                running_uuts += 1
                uut_item.poll_delay = 5
                SCRN.add(f'{{GREEN}}{uut_item.state}{{RESET}}:')
            elif uut_item.state == 'ARM':
                armed_uuts += 1
                SCRN.add(f'{{ORANGE}}{uut_item.state}{{RESET}}:')
            else:
                SCRN.add(f'{{RED}}{uut_item.state}{{RESET}}:')
            SCRN.end()
        
            for stream in uut_item.streams.items():
                sstate = uut_item.get_stream_state(stream[0])
                sites = stream[1]['all_sites']
                rport = stream[1]['rport']
                SCRN.add(f'{{TAB}}{sites}:{rport}{{ORANGE}} --> {{RESET}}afhba.{stream[0]}')
                SCRN.add(f'{{TAB}}{{BOLD}}{sstate.rx_rate * args.buffer_len}MB/s Total Buffers: {int(sstate.rx) * args.buffer_len:,} Status: {sstate.STATUS}{{RESET}}')
                SCRN.end()
                if args.check:
                    name, result = uut_item.get_results(stream[0])
                    SCRN.add_line(f'{{TAB}}{{TAB}}{name} {result}')
        
                if sstate.STATUS == 'STOP_DONE':
                    ended_streams += 1
                   
        return armed_uuts, running_uuts, ended_streams, armed_uuts == len(uut_collection), running_uuts == len(uut_collection)
    return hot_run_status_update
                   
def dry_run(args, uut_collection):
    top_uut = uut_collection[0].api
    
    for uut_item in uut_collection:
        uut_item.configure()
    if args.wrtd_txi is not None:        
        print(f'wrtd: {args.wrtd_txi}')
        top_uut.cC.sr(args.wrtd_txi) 
    exit(PR.Yellow('Dry Run Complete'))    


def hot_run(SCRN, args, uut_collection, configure_host):
    total_streams = hot_run_init(uut_collection)
    sec_count = 0
    all_running = False
    all_armed = False
    cycle_max = 0.5
    time_start = time.time()
    release_trigger_when_ready = release_trigger_when_ready_wrapper(SCRN, args, uut_collection)
    hot_run_status_update = hot_run_status_update_wrapper(SCRN, args, uut_collection)
    
    try:
        while True:
            cycle_start = time.time()
            stopping = False

            SCRN.add_line('')
            SCRN.add('{REVERSE} ')
            if args.secs and all_running:
                if not sec_count:
                    time_start = time.time()
                sec_count = time.time() - time_start
                if args.secs <= 60:
                    SCRN.add("{0:.1f}/{1} secs ", sec_count, args.secs)
                else:
                    c_mins, c_secs = divmod(sec_count, 60)
                    SCRN.add(f"{int(c_mins)}:{int(c_secs):02}/{int(args.t_mins)}:{int(args.t_secs):02} mins ")
                SCRN.add(f"Buffer Length: {args.buffer_len}MB ")
            else:
                SCRN.add("{0:.0f} secs ",time.time() - time_start)
                SCRN.add("Max: {0}MB Buffer Length: {1}MB ", args.nbuffers * args.buffer_len, args.buffer_len)

            if release_trigger_when_ready(all_armed) < 0:
                break
            
            armed_uuts, running_uuts, ended_streams, all_armed, all_running = hot_run_status_update()

            if sec_count and time.time() - time_start > args.secs:
                SCRN.add_line('{BOLD}Time Limit Reached Stopping{RESET}')
                stopping = True
                if running_uuts == 0:
                    SCRN.render(False)
                    break
                stop_uuts(uut_collection)

            if not stopping and ended_streams == total_streams:
                SCRN.add_line('{BOLD}Buffer limit Reached Stopping{RESET}')
                if running_uuts == 0:
                    SCRN.render(False)
                    break
                stop_uuts(uut_collection)

            SCRN.render()
            cycle_length = time.time() - cycle_start
            sleep_time = 0 if cycle_length > cycle_max else cycle_max - cycle_length
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        SCRN.render_interrupted()
        PR.Red('Interrupt!')
        stop_uuts(uut_collection)
    except Exception as e:
        SCRN.render_interrupted()
        PR.Red('Fatal Error')
        stop_uuts(uut_collection)
        print(e)
    time.sleep(1)
    print('Done')
        
def run_main(args):
    uut_collection = object_builder(args)
    configure_host(uut_collection, args)

    if args.dry_run:
        dry_run(args, uut_collection)
    else:
        hot_run(DISPLAY(), args, uut_collection, configure_host)


if __name__ == '__main__':
    run_main(get_parser().parse_args())
