#!/usr/bin/env python3

import argparse
import acq400_hapi
import time
import numpy as np
from prettytable import PrettyTable

"""
Usage:
    ./test_apps/DI_tester.py acq2106_999
    ./test_apps/DI_tester.py acq2106_999 --live=1 --sites=1
"""

def run_main(args):
    uut = acq400_hapi.factory(args.uut)
    nchan = int(uut.s0.NCHAN)
    mchan = 32
    spad = int(uut.s0.spad.split(',')[1])
    spad_start = nchan - spad
    sites = get_sites(uut, args)
    all_results = PrettyTable(['Channel', 'Max', 'Min', 'Mean', 'length'])
    all_results.title = f"{args.uut} DI"

    if args.live:
        for buff in uut.stream(recvlen=args.buflen*nchan, data_size=4):
            for site in sites:
                start_chan = (site - 1) * mchan
                end_chan = site * mchan
                for idx in range(start_chan, end_chan, 1):
                    max, min, mean, length = get_stats(buff[idx::nchan])
                    all_results.add_row([idx + 1, max, min, mean, length])
            print(all_results)
            if spad:
                print(f"Spad[0] {buff[spad_start::nchan][0]} - {buff[spad_start::nchan][-1]}")
            all_results.clear_rows()
        return

    print(f"Testing {args.uut}")
    for site in sites:
        if args.ask:
            control_analog_interface(site)

        buff = next(uut.stream(recvlen=4096*nchan, data_size=4))
        results = PrettyTable(['Channel', 'Max', 'Min', 'Mean', 'length'])
        results.title = f"Site {site}"
        start_chan = (site - 1) * mchan
        end_chan = site * mchan

        for idx in range(start_chan, end_chan, 1):
            max, min, mean, length = get_stats(buff[idx::nchan])
            tweaked_chan = idx % mchan + 1
            results.add_row([tweaked_chan, max, min, mean, length])
            all_results.add_row([idx + 1, max, min, mean, length])

        print(results)
        all_results.add_row(['-', '-', '-', '-', '-'])

    time.sleep(1)
    print(all_results)
    filename = f"{args.uut}_DI_results_{int(time.time())}.csv"
    with open(filename, 'w', newline='') as file:
        print(f"Writing results to {filename}")
        file.write(all_results.get_csv_string())

def get_stats(arr):
    arr = np.delete(arr, 0)
    max = np.amax(arr)
    min = np.amin(arr)
    mean = int(np.mean(arr))
    length = len(arr) + 1
    return max, min, mean, length

def get_sites(uut, args):
    if(args.sites):
        return list(map(int , args.sites.split(',')))
    return uut.get_site_types()['DIOSITES']

def control_analog_interface(site):
    question = f"Is SigGen connected to site {site}: "
    while True:
        ans = input(question)
        if(ans.startswith('y')):
            break

def get_parser():
    parser = argparse.ArgumentParser(description='DI Tester')
    parser.add_argument('--buflen', default=4096 , type=int, help="Buffer len")
    parser.add_argument('--live', default=0, type=int, help="Live output")
    parser.add_argument('--ask', default=1, type=int, help="Ask for connection")
    parser.add_argument('--sites', default=None, help="Sites to use ie 1,2,3")
    parser.add_argument('uut', help="uut")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
