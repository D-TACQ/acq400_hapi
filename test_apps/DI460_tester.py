#!/usr/bin/env python3

import argparse
import acq400_hapi
from acq400_hapi.acq400_print import PR

"""
Usage:
    ./test_apps/DI460_tester.py --DI=1 --stim=5 --test=1 --verbose=1 acq2206_018
"""

def get_parser():
    parser = argparse.ArgumentParser(description='DI460ELF_tester')
    parser.add_argument('--DI', default=1, type=int, help="DI site")
    parser.add_argument('--stim', default=5, type=int, help="stim site")
    parser.add_argument('--test', default=3, type=int, help="1 first pass, 2 second pass, 3 both")
    parser.add_argument('--verbose', default=0, type=int, help="Increase verbosity")
    parser.add_argument('uut_name', help="uut")
    return parser

correct_signals = {
    'A' : '0x000061a8',
    'B' : '0x000030d4'
}

def run_main(args):
    uut = acq400_hapi.factory(args.uut_name)
    print(f"Testing {args.uut_name}")
    print(f"\tDI: site {args.DI}")
    print(f"\tStim: Site {args.stim}")
    print()

    if 1 & args.test:
        PR.Yellow('First pass test')
        verify_connections(get_connections(uut, args.DI), args)
        check_signals(get_signals(uut, args.DI), [1,2,3], args)
        check_loopback(uut, [4,5,6], args)
        PR.Green('First pass test passed')

    if 1 & args.test and 2 & args.test:
        print()
        PR.Yellow('Reorder cables and press enter')
        input()

    if 2 & args.test:
        PR.Yellow('Second pass test')
        verify_connections(get_connections(uut, args.DI), args)
        check_signals(get_signals(uut, args.DI), [4,5,6], args)
        check_loopback(uut, [1,2,3], args)
        PR.Green('Second pass test passed')

def get_connections(uut, site_num):
    connections = {}
    site = getattr(uut, f"s{site_num}")
    for port in range(1, 7):
        knob = f"HDMI_{port}_POS_CON"
        connections[port] = bool(int(site.__getattr__(knob)))
    return connections

def verify_connections(connections, args):
    error = False
    for num, status in connections.items():
        if not status:
            PR.Red(f"Error: HDMI {num} not connected")
        elif args.verbose:
            PR.Green(f"HDMI {num} connected")
    if error:
        exit()
    PR.Green('All HDMI Cables are plugged in')

def get_signals(uut, site_num):
    signals = {}
    site = getattr(uut, f"s{site_num}")
    for port in range(1, 7):
        signals[port] = {}
        knob = f"cnt_{port}"
        signals[port]['A'] = site.__getattr__(knob)
        knob = f"cnt_{port + 6}"
        signals[port]['B'] = site.__getattr__(knob)
    return signals

def check_signals(signals, ports, args):
    error = False
    for port in ports:
        for signal, value in signals[port].items():
            difference = abs(int(correct_signals[signal], 16) - int(value, 16))
            if difference > 10:
                error = True
                PR.Red(f"Error: Signal[{port}:{signal}] is {value} not {correct_signals[signal]}")
            elif args.verbose:
                print(f"Pass: Signal[{port}:{signal}] is {value}")
    if error:
        exit()
    PR.Green(f"A&B signals on HDMI {ports} are correct")

def check_loopback(uut, ports, args):
    cable_errors = [0, 0, 0]
    error = False
    idx = 5 if sum(ports) > 10 else 6
    stim_site =  getattr(uut, f"s{args.stim}")
    DI_site =  getattr(uut, f"s{args.DI}")
    for stim_value in range(8):
        stim_bits = f"0x{stim_value}00"
        stim_site.stim_bits = stim_bits
        register = DI_site.di_snoop
        reg_bit = int(register[idx-1 : idx])
        if reg_bit != stim_value:
            error = True
            cable_errors = find_bad_cables(stim_value, reg_bit, cable_errors)
        if args.verbose:
            print(f"Loopback results stim_bits: {stim_bits} register_bit: {reg_bit}")
    for i, cable_error in enumerate(cable_errors):
        if cable_error:
            PR.Red(f"Error: Looback on HDMI {ports[i]} Failed")
    if error:
        exit()
    PR.Green(f"Loopbacks on HDMI {ports} are correct")

def find_bad_cables(stim_value, reg_bit, cable_errors):
    xor_bit = stim_value ^ reg_bit
    pos = 0
    length = xor_bit.bit_length()
    while pos < length:
        if xor_bit & 1:
            cable_errors[pos] += 1
        xor_bit = xor_bit >> 1
        pos += 1
    return cable_errors

if __name__ == '__main__':
    run_main(get_parser().parse_args())

