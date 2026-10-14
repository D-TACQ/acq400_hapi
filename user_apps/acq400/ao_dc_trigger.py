#!/usr/bin/env python3

"""
Set a value to output on dacs on trigger

Usage:
    # Set immediate value and triggered using hex
    ./user_apps/acq400/ao_dc_trigger.py 0x0000,0x0000,0x0000,0x0000 0x1fff,0x3fff,0x5fff,0x7fff acq1001_070

    # Set immediate value and triggered using floats
    ./user_apps/acq400/ao_dc_trigger.py 0,0,0,0 0.75,1.5,2.25,3 acq1001_070

    # Set immediate value only (only valid after triggered)
    ./user_apps/acq400/ao_dc_trigger.py 0,0,0,0 acq1001_070
"""

import argparse
import acq400_hapi

def main(args):

    def comma_separated_hexes(value):
        values = value.split(',')
        for idx, value in enumerate(values):
            if not value.lower().startswith('0x'):
                values[idx] = convert_voltage(float(value), args.encoding, args.vmin, args.vmax, args.bits)
        return ','.join(values)

    uut = acq400_hapi.factory(args.uutname)

    if args.triggered:
        #if triggered not empty
        uut.s1.low_latency = 0
        uut.s1.dac_enable = 0
        uut.s1.__reset_fifo = 1
        uut.s1.dac_enable = 1
    elif not args.triggered and uut.s1.is_triggered == '0':
        #if triggered empty and not triggered
        print(f"Error: must run with triggered value before clear")
        return

    if args.initial:
        initial = comma_separated_hexes(args.initial)
        print(f'Set Initial: {initial}')
        uut.s1.NOIMM_AO_ALL_UNIQUE = initial

    if args.triggered:
        triggered = comma_separated_hexes(args.triggered)
        print(f'Set Triggered: {triggered}')
        uut.s1.NOIMM_AO_ALL_UNIQUE = triggered
        print("soft_trigger when ready")

def convert_voltage(v, encoding, vmin, vmax, bits):
    # Clamp voltage to configured range
    v = max(vmin, min(vmax, v))

    # Calculate normalized position (0.0 to 1.0)
    span = vmax - vmin
    norm = 0.0 if span == 0 else (v - vmin) / span

    max_val = (1 << bits) - 1
    half_range = 1 << (bits - 1)

    if encoding == "twos_complement":
        # Signed range mapping
        val = round(norm * max_val - half_range)
        if val < 0:
            val += (1 << bits)
    elif encoding == "offset_binary":
        # Unsigned range mapping
        val = round(norm * max_val)
    else:
        raise ValueError(f"Unknown encoding: {encoding}")

    # Dynamically calculate hex width based on bits (e.g., 16-bit -> 4 hex chars, 12-bit -
    hex_width = (bits + 3) // 4
    return f"0x{val:0{hex_width}X}"


def get_parser():
    parser = argparse.ArgumentParser(description='Set a value to output on dacs on trigger')
    parser.add_argument('--bits', default=16, type=int, help='Resolution in bits (e.g., 8, 12, 16, 24)')
    parser.add_argument('--vmin', default=0.0, type=float, help='Voltage min')
    parser.add_argument('--vmax', default=3.3, type=float, help='Voltage Max')
    parser.add_argument('--encoding', choices=('offset_binary', 'twos_complement'), default='offset_binary', help='Encoding: twos_complement signed range (-32768 to 32767 for 16-bit) or offset_binary unsigned range (0 to 65535 for 16-bit)')

    parser.add_argument('initial', type=str, help='First sample NOWAIT')
    parser.add_argument('triggered', type=str, nargs='?', help='First sample after trigger')
    parser.add_argument('uutname', help='UUT hostname')
    return parser

if __name__ == '__main__':
    main(get_parser().parse_args())