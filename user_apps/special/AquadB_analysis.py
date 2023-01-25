#!/usr/bin/env python3

import argparse
import os
import sys
import argparse

from acq400_hapi import PR, Acq400UI
import user_apps.special.run_AquadB_movement as MOVE
import user_apps.analysis.host_demux as DEMUX

from prettytable import PrettyTable as PT
import numpy as np

"""
    example cmd
    ./user_apps/special/AquadB_analysis.py --ecolumn=DI6 --run_test=yes --silence=YES acq2106_999

    ./user_apps/special/AquadB_analysis.py --stim=acq2106_888 --dwg=dat_files/dwg123 --run_test=yes --silence=NO acq2106_999

    args for subordinate scripts should pass through wrapper
"""

wrapper_args = None

def main(args):
    global wrapper_args

    PR.Yellow("Running Host_Demux: pses={} pcfg={}".format(args.pses, args.pcfg))
    PR.Yellow("Running Host_Demux: stim={} dwg={}".format(args.stim, args.dwg))

    wrapper_args = args
    if args.run_test.upper() == 'YES':
        #aquadb_args = aquadb_move_args()
        blockPrint()
        MOVE.main(args)
        enablePrint()

    # hazard: MOVE callback and DEMUX callback have different signatures, so args.callback MUST be null for MOVE
    args.callback = homecoming
    #demux_args = host_demux_args()
    blockPrint()
    DEMUX.run_main(args)
    enablePrint()

def aquadb_move_args(parser):
    parser = MOVE.get_parser(parser)
    default_args = {
        'force_delete' : 1,
        'root': '../AquadB_FAT/DATA',
        'stim': 'acq2106_351',
        'dwg': '../AquadB/DWG/wiggle',
        'verbose': 2
    }
    parser = Acq400UI.imported_defaults_overrider(parser,default_args)
    return parser

def host_demux_args(parser):
    parser = DEMUX.get_parser(parser)
    default_args = {
        'src' : '../AquadB_FAT/DATA',
        'pcfg': '../AquadB_FAT/PCFG/qen_and_wr_and_di.pcfg',
        'pses': '1:-1:1',
        'plot': 0
    }
    parser = Acq400UI.imported_defaults_overrider(parser,default_args)
    return parser


def blockPrint():
    if wrapper_args.silence.upper() == 'YES':
        sys.stdout = open(os.devnull, 'w')

def enablePrint():
    if wrapper_args.silence.upper() == 'YES':
        sys.stdout = sys.__stdout__

def get_events(data):
    arr_name = wrapper_args.ecolumn
    if arr_name not in data:
        PR.Red('Warning: Event array "{}" not found'.format(arr_name))
        return []
    event_arr = data[arr_name]
    lower = event_arr[0]
    arr_len = len(event_arr)
    consecutive = False
    events = []
    events.append(0)
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
    return output

def homecoming(data):
    enablePrint()
    PR.Green('Homecoming')
    events = get_events(data)
    if len(events) == 0:
        PR.Red('Warning: No events found')
        return
    build_table(events,data)

def get_parser():
    parser = argparse.ArgumentParser(description='Wrapper for move aquadb and host demux')
    parser.add_argument('--run_test', default='YES', help="whether or not to run the test")
    parser.add_argument('--ecolumn', default=None, help="Event column")
    parser.add_argument('--silence', default='YES', help='Hide subordinate script output')
    parser.add_argument('uuts', nargs='+', help='uuts - for auto configuration data_type, nchan, egu or just a label')
    aquadb_move_args(parser)
    host_demux_args(parser)
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())
