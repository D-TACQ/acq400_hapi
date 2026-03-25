#!/usr/bin/env python3

"""
Plot STL files

Usage:
    ./user_apps/utils/plot_stl.py STL/sos0.stl --rep=2
    ./user_apps/utils/plot_stl.py STL/ramp_1step_64samp.stl --ndo=4

"""

import argparse
import matplotlib.pyplot as plt
import numpy as np

def run_main(args):

    stl_def = []
    hex_max = ''

    with open(args.stl, 'r') as fp:
        for line in fp:

            line = line.split('#')[0].strip()
            if not line: continue
            pos, state = line.split(',')
            if not stl_def: pos = '0'

            bitmask = hex_to_bitmask(state)
            if len(state) > len(hex_max): hex_max = state

            last_pos = 0
            if pos.startswith('+'): last_pos += stl_def[-1][0] if stl_def else 0
            stl_def.append((int(pos) + last_pos, state, bitmask))

    last_pos = stl_def[-1][0]
    bits = len(hex_to_bitmask(hex_max))
    if args.ndo > bits: args.ndo = bits
    data = np.zeros((bits, last_pos), dtype=bool)

    for idx, (pos, hex, mask) in enumerate(stl_def):

        next_pos = stl_def[idx + 1][0] if idx + 1 < len(stl_def) else None
        data[:, pos:next_pos] = np.array(mask[::-1])[:, None]

        print(f"transition {pos} = {hex}")

    fig, axes = plt.subplots(args.ndo, 1, figsize=(10, 2 * args.ndo), sharex=True, squeeze=False)

    if args.rep < 0: args.rep = 0
    for idx, dat in enumerate(data):
        if idx >= args.ndo: continue
        axes[idx][0].plot(np.tile(dat, args.rep + 1))
        axes[idx][0].set_ylabel(f"DO{idx}")
    plt.show()

def hex_to_bitmask(hex_str: str):
    value = int(hex_str, 16)
    width = len(hex_str) * 4
    bits = format(value, f"0{width}b")
    return [int(b) for b in bits]

def get_parser():
    parser = argparse.ArgumentParser(description='Plot STL file')
    parser.add_argument('--ndo', default='1', type=int, help='Number of DOs to plot')
    parser.add_argument('--rep', default='0', type=int, help='Times to repeat the STL')
    parser.add_argument('stl', help="STL filename")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())