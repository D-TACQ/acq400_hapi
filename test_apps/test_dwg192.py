#!/usr/bin/env python3
"""
./test_apps/test_dwg192.py --awg_file=ramp65536_1_2_16.dat --dwg=acq2106_387 --sig_gen=SG0106 --shots=1 --tester=acq2106_130
"""

import os
import numpy as np
import argparse
import acq400_hapi
import time
import matplotlib.pyplot as plt
from prettytable import PrettyTable

def get_parser():
    parser = argparse.ArgumentParser(description='checks rising edge index on dwg output')

    parser.add_argument('--shots', default=100, type=int, help='number of shots to run')
    parser.add_argument('--comsites', default='1,2' , help='sites to compare on test box')
    parser.add_argument('--sig_gen', required=True , help='signal gen')
    parser.add_argument('--awg_file', required=True , help='awg file')
    parser.add_argument('--dwg', required=True , help='dwg uut')
    parser.add_argument('--tester', required=True , help="test uut")
    return parser

def run_main(args):
    tester_uut = acq400_hapi.factory(args.tester)
    dwg_uut = acq400_hapi.factory(args.dwg)

    dwg_uut.s0.SIG_SRC_TRG_0 = 0
    tester_uut.s0.transient = 'DEMUX=1'

    site_map = build_site_map(tester_uut, args.comsites)

    errors = 0
    filename = f'{args.dwg}_dwg_results.csv'

    header = ['Channel']
    header.extend(map(lambda x: f'site {x}', site_map.keys()))
    header.append('Error')

    all_sites = []
    for site in site_map:
        all_sites.extend(site_map[site]['channels'])

    for shot in range(args.shots):
        print(f'Starting shot {shot + 1}/{args.shots}')
        load_awg(dwg_uut, args)
        wait_for_arm(tester_uut)
        trigger_sig(args.sig_gen)

        time.sleep(1)
        channels_data = tester_uut.read_channels(all_sites)
        print(channels_data)
        t = PrettyTable(header)
        t.title = f'dwg::{args.dwg} --> test::{args.tester}'
        for idx, channel in enumerate(site_map[1]['channels']):
            row = [channel]
            indexes = []
            for site in site_map:
                #print(f'idx{idx} channel{channel} site{site}')
                indexes.append(get_rising_idx(channels_data[site_map[site]['channels'][idx] - 1]))

            row.extend(indexes)
            if not indexes.count(indexes[0]) == len(indexes):
                errors += 1
                row.append('Error')
            else:
                row.append('')

            t.add_row(row)

        print(t)
        with open(filename, 'a') as f:
            f.write(t.get_csv_string())
        print(f'{errors} Errors')

    with open(filename, 'a') as f:
        f.write(f'{errors} Errors Total')
    print('Done')

def load_awg(uut, args):
    print('Loading awg file')
    if not os.path.isfile(args.awg_file):
        exit('awg file not found')
    awg = np.fromfile(args.awg_file, dtype=np.int32)
    uut.load_awg(awg, autorearm=False)

def wait_for_arm(uut):
    uut.s0.set_arm = 1
    print(f'Waiting to arm {uut.s0.HN}')
    while True:
        state = uut.s0.CONTINUOUS_STATE.split('CONTINUOUS:STATE ')[1]
        if(state == 'ARM'):
            print('Armed')
            return
        time.sleep(1)

def trigger_sig(sig_gen):
    print('Triggering sig gen')
    acq400_hapi.Agilent33210A(sig_gen).trigger()

def build_site_map(uut, site_nums):
    site_map = {}
    sites = map(int, site_nums.split(','))
    for idx in sites:
        site_id = f's{idx}'
        site = getattr(uut, site_id)
        nchan = int(site.NCHAN)
        offset = nchan * (idx - 1) + 1
        site_map[idx] = {}
        site_map[idx]['nchan'] = nchan
        site_map[idx]['channels'] = list(range(offset, offset + nchan))
    return site_map

def get_rising_idx(array):
    return  np.argmax(array>10)

if __name__ == '__main__':
    run_main(get_parser().parse_args())