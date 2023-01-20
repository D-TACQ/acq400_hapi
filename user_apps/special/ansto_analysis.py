#!/usr/bin/env python3

import argparse
import os
import sys
import argparse

from acq400_hapi import PR
import user_apps.special.run_AquadB_movement as MOVE
import user_apps.analysis.host_demux as DEMUX

from prettytable import PrettyTable as PT
import numpy as np

"""
    example cmd
    ./ansto_analysis.py --ecolumn=DI6 --run_test=yes --silence=YES acq2106_999

    ./ansto_analysis.py --stim=acq2106_888 --dwg=dat_files/dwg123 --run_test=yes --silence=NO acq2106_999
    
    args for subordinate scripts should pass through wrapper
"""

wrapper_args = None

def main(args):
    global wrapper_args
    wrapper_args = args
    if args.run_test.upper() == 'YES':
        aquadb_args = aquadb_move_args()
        blockPrint()
        MOVE.main(aquadb_args)
        enablePrint()

    demux_args = host_demux_args()
    blockPrint()
    DEMUX.run_main(demux_args)
    enablePrint()

def aquadb_move_args():
    parser = MOVE.get_parser()
    default_args = {
        'force_delete' : 1,
        'root': '/home/dt100/DATA',
        'stim': 'acq2106_274',
        'dwg': 'dat_files/wiggle.2x32',
        'verbose': 2
    }
    parser = imported_defaults_overrider(parser,default_args)   
    args = parser.parse_known_args()[0]
    PR.Yellow("Running AquadB_movement: stim={} dwg={}".format(args.stim,args.dwg))
    return args

def host_demux_args():
    parser = DEMUX.get_parser()
    default_args = {
        'src' : '/home/dt100/DATA',
        'pcfg': 'PCFG/ansto_qen_and_di.pcfg',
        'pses': '1:-1:1',
        'plot': 0
    }    
    parser = imported_defaults_overrider(parser,default_args)
    args = parser.parse_known_args()[0]
    args.callback = homecoming
    PR.Yellow("Running Host_Demux: pses={} pcfg={}".format(args.pses,args.pcfg))
    return args

def imported_defaults_overrider(parser,defaults):
    arr = parser._positionals._actions
    for x in arr:
        if x.dest in defaults.keys():
            #print("Overriding {} with {}".format(x.dest,defaults[x.dest]))
            x.default = defaults[x.dest]
    return parser

def blockPrint():
    if wrapper_args.silence.upper() == 'YES':
        sys.stdout = open(os.devnull, 'w')

def enablePrint():
    if wrapper_args.silence.upper() == 'YES':
        sys.stdout = sys.__stdout__

def print_numpy_arrays(data):
    keys = data.keys()
    for key in keys:
        print("\033[93m{}\033[00m: {} \033[93m Length: {}\033[00m".format(key,data[key],len(data[key])))

def get_events(data):
    arr_name = wrapper_args.ecolumn
    if arr_name not in data:
        exit(PR.Red('Error: Array "{}" not found'.format(arr_name)))
    event_arr = data[arr_name]
    lower = event_arr[0]
    arr_len = len(event_arr)
    consecutive = False
    events = []
    for i in range(arr_len):
        if event_arr[i] > lower:
            if not consecutive:
                consecutive = True
                events.append(i)
        else:
            consecutive = False
    if len(events) == 0:
        return []
    PR.Purple("{} Low: {} High: {} Length: {}".format(arr_name,lower,event_arr[events[0]],arr_len))
    return events

def build_table(events,data):
    arr_name = wrapper_args.ecolumn
    events = demarcate(events)
    t = PT()
    t.add_column('events({})'.format(arr_name),events)
    for arr in data:
        if arr != arr_name:
            new_column = []
            for ev in events:
                if ev == '-':
                    new_column.append(ev)
                    continue
                value = data[arr][ev]
                value = round(value, 2)
                new_column.append(value)
            t.add_column(arr,new_column)
    t.align = 'r'
    print(t)

def demarcate(events):
    gap = 1000
    pre = events[0]
    output = []
    for num in events:
        if num - pre > gap:
            output.append('-')
        output.append(num)
        pre = num
    if output[1] != '-':
        output.insert(1,'-')
    return output
    
def homecoming(data):
    enablePrint()
    PR.Green('Homecoming')
    #print_numpy_arrays(data)
    events = get_events(data)
    if len(events) == 0:
        exit('No events found')
    build_table(events,data)

def get_parser():
    parser = argparse.ArgumentParser(description='Wrapper for move aquadb and host demux')
    parser.add_argument('--run_test', default='YES', help="whether or not to run the test")
    parser.add_argument('--ecolumn', default='DI6', help="Event column")
    parser.add_argument('--silence', default='YES', help='Hide subordinate script output')
    parser.add_argument('uut', help='uut - for auto configuration data_type, nchan, egu or just a label')
    return parser

if __name__ == '__main__':
    main(get_parser().parse_known_args()[0])
