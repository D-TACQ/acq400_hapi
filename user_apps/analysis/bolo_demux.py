#!/usr/bin/env python3

"""

Plot and save BOLO cal or cap data

Usage:
    # Plot cal data
    ./user_apps/analysis/bolo_demux.py --mode=CAL --chans=1-8 acq2106_123

    # Plot and save cap data
    ./user_apps/analysis/bolo_demux.py --mode=CAP --chans=1-8 --save acq2106_123

"""

import argparse
import os
import numpy as np
from acq400_hapi import ArgTypes, factory
from matplotlib import pyplot as plt


BOLO_SAMPLE_RATE = 10_000

def main(args):

    uut = factory(args.uutname)

    calibrated = args.mode == 'CAL'
    nchan = int(uut.s0.NCHAN) // 3

    dtype = []
    for chan in range(1, nchan + 1):
        dtype.append((f'{chan}_MAG', np.int32))
        dtype.append((f'{chan}_PHI', np.int32))
        if calibrated:
            dtype.append((f'{chan}_OHI', np.int16))
            dtype.append((f'{chan}_OHV', np.int16))
        else:
            dtype.append((f'{chan}_PWR', np.int32))
    dtype = np.dtype(dtype)

    data = uut.read_channels()
    data = np.ascontiguousarray(data.T).view(dtype).reshape(-1)

    print(f"[{uut.uut}]: Read {data.nbytes} Bytes {nchan} Chans")

    if args.save:
        mode = 'CAL' if calibrated else 'CAP'
        os.makedirs(args.root, exist_ok=True)
        for field in data.dtype.names:
            filename = f"{uut.uut}.{field}.{mode}.dat"
            filepath = os.path.join(args.root, filename)
            print(f"Saving {field} to {filepath}")
            data[field].tofile(filepath)


    row_names = ['MAG', 'PHI', 'OHI', 'OHV'] if calibrated else ['MAG', 'PHI', 'PWR']

    row_formats = {
        'MAG': {
            'title': 'Magnitude',
            'ylabel': 'mV',
            'scaler': args.mag_sf,
        },
        'PHI': {
            'title': 'Phase',
            'ylabel': 'RAD',
            'scaler': args.phi_sf,
        },
        'OHI': {
            'title': 'Ohmic Heating Current',
            'ylabel': 'mA',
            'scaler': args.ohi_sf,
        },
        'OHV': {
            'title': 'Ohmic Heating Volts',
            'ylabel': 'V',
            'scaler': args.ohv_sf,
        },
        'PWR': {
            'title': 'Power',
            'ylabel': 'mW',
            'scaler': args.pwr_sf,
        },
    }

    fig, axes = plt.subplots(len(row_names), 1, sharex=True, figsize=(10, 8))

    x = np.arange(len(data))
    xlabel = 'Samples'
    if args.secs:
        x = x / BOLO_SAMPLE_RATE
        xlabel = 'Seconds (s)'
    x = x[args.skip:]

    for ax, row_name in zip(axes, row_names):
        print(f"Plotting CH{args.chans} {row_name}")
        format = row_formats[row_name]
        ax.set_title(format['title'])
        ax.set_ylabel(format['ylabel'])
        for chan in args.chans:
            ax.plot(x, data[f'{chan}_{row_name}'][args.skip:] * format['scaler'], label=f'CH{chan}')
        ax.legend(loc='upper right')

    axes[-1].set_xlabel(xlabel)
    fig.suptitle(f"{args.uutname} BOLO {args.mode}")
    fig.tight_layout()
    plt.show()

def get_parser():
    parser = argparse.ArgumentParser(description="Plot and save BOLO cal or cap data")
    parser.add_argument('uutname',  help="uut hostname")
    parser.add_argument('--mode',  default='CAL', choices=('CAL', 'CAP'), help="UUT Mode")
    parser.add_argument('--chans', default=[1], type=ArgTypes.list_of_channels, help='Channels to plot')
    parser.add_argument('--skip', default=20, type=int, help='Skip samples from start of channel')
    parser.add_argument('--secs', action='store_true', help='Plot in seconds')
    parser.add_argument('--save', action='store_true', help='Save data to disk')
    parser.add_argument('--root', default='BOLO_DATA', help='Save root')

    parser.add_argument('--mag_sf', default=7.109e-05, type=float, help='Magnitude scaling factor')
    parser.add_argument('--phi_sf', default=1.8626e-09, type=float, help='Phase scaling factor')
    parser.add_argument('--pwr_sf', default=4.550e-03, type=float, help='Power scaling factor')
    parser.add_argument('--ohi_sf', default=2.6041666e-3, type=float, help='Ohmic heating current scaling factor')
    parser.add_argument('--ohv_sf', default=3.81469725e-5, type=float, help='Ohmic heating voltage scaling factor')

    return parser


if __name__ == "__main__":
    main(get_parser().parse_args())
