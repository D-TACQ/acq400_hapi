#!/usr/bin/env python3

"""
Overview:
reads awg rtm stream datafile and compares first set of bursts against all subsequent bursts
plots first burst that is outside tolerance
translen should be UUT translen * number of AWG files

Usage:
    ./test_apps/check_awg_rtm_bursts.py --translen=$((10048 * 8)) --file=awg_rtm_stream.dat  --nchan=32
"""


import argparse
import numpy as np
import matplotlib.pyplot as plt
import os


def run_main(args):
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return 1

    if args.plot_bursts is not None:
        burst_start, burst_end = args.plot_bursts
        print(burst_start + burst_end)
        plot_burst(
            args.file,
            translen=args.translen,
            datasize=args.datasize,
            nchan=args.nchan,
            burst_start=burst_start,
            burst_end=burst_end,
        )
        return 0
    
    dtype = np.int16 if args.datasize == 2 else np.int32
    max_scale = np.iinfo(dtype).max
    atol = int(max_scale * args.tolerance / 100.0)
    
    first_burst = read_burst(args.file, args.translen, args.datasize, args.nchan)
    
    target_sample = check_burst(
        args.file, first_burst, args.translen, args.datasize, args.nchan, atol, rate_mode=args.rate, skip_bursts=args.skip
    )
    
    if args.rate: return 0
    
    if target_sample is None: 
        print("Burst check passed!")
        return
    
    aligned_sample = (target_sample // args.translen) * args.translen
    burst_num = aligned_sample // args.translen
    print(f"Error: bad burst #{burst_num} (sample {aligned_sample:,})")

    burst_neighbours = 2
    burst_start = max(0, burst_num - burst_neighbours)
    burst_end = burst_num + burst_neighbours

    if args.compare:
        plot_compare(args.file, target_sample, args.translen, args.datasize, args.nchan, first_burst, atol=atol)
    plot_burst(
        args.file,
        translen=args.translen,
        datasize=args.datasize,
        nchan=args.nchan,
        burst_start=burst_start,
        burst_end=burst_end,
    )


def read_burst(filename, translen, datasize, nchan):
    bytes_per_sample = datasize * nchan
    num_bytes = translen * bytes_per_sample
    
    with open(filename, 'rb') as f:
        burst_bytes = f.read(num_bytes)
    
    if len(burst_bytes) < num_bytes:
        raise ValueError(f"File too small: only {len(burst_bytes)} bytes, need {num_bytes}")
    
    dtype = np.int16 if datasize == 2 else np.int32
    burst_raw = np.frombuffer(burst_bytes, dtype=dtype)

    return burst_raw

def check_burst(filename, burst, translen, datasize, nchan, atol, rate_mode=False, skip_bursts=0):
    file_size = os.path.getsize(filename)
    bytes_per_sample = datasize * nchan
    total_samples = file_size // bytes_per_sample
    total_bursts = total_samples // translen
    burst_length = len(burst)
    bad_bursts = [] if rate_mode else None
    
    start_sample = (skip_bursts if skip_bursts > 0 else 1) * translen
    checked_bursts = total_bursts - skip_bursts if skip_bursts > 0 else total_bursts - 1
    current_sample = start_sample
    
    while current_sample < total_samples:
        aligned_sample = (current_sample // translen) * translen
        
        if aligned_sample < current_sample:
            aligned_sample += translen
        
        if aligned_sample >= total_samples:
            break
        
        burst_raw = read_chunk(filename, aligned_sample, translen, datasize, nchan)
        
        if len(burst_raw) != burst_length:
            current_sample = aligned_sample + translen
            continue
        
        diff = np.abs(burst_raw - burst)
        exceeds_tolerance = diff > atol
        mismatch_count = np.sum(exceeds_tolerance)
        
        if mismatch_count > 0:
            burst_num = aligned_sample // translen
            max_diff = np.max(diff)
            bad_bursts.append(aligned_sample)
            print(f"Mismatch detected: Sample {aligned_sample:,} Burst #{burst_num} {mismatch_count} values exceed tolerance (max diff: {max_diff}, atol: {atol})")
            if not rate_mode: return aligned_sample
        
        current_sample = aligned_sample + translen
        progress_pct = (current_sample / total_samples) * 100
        print(f"\rChecking sample {current_sample:,} / {total_samples:,} ({progress_pct:.1f}%)", end='', flush=True)
    
    print()
    
    if rate_mode:
        bad_count = len(bad_bursts)
        if bad_count == 0: print(f"Burst check passed! All {checked_bursts} bursts matched.")
        else:
            bad_pct = (bad_count / checked_bursts) * 100.0
            print(f"Out of {checked_bursts} bursts, {bad_count} were bad ({bad_pct:.2f}%)")
        return None
    
    return None

def read_chunk(filename, start_sample, num_samples, datasize, nchan):
    bytes_per_sample = datasize * nchan
    start_byte = start_sample * bytes_per_sample
    num_bytes = num_samples * bytes_per_sample
    
    with open(filename, 'rb') as f:
        f.seek(start_byte)
        chunk_bytes = f.read(num_bytes)
    
    if len(chunk_bytes) == 0:
        return np.array([], dtype=np.int16 if datasize == 2 else np.int32)
    
    dtype = np.int16 if datasize == 2 else np.int32
    return np.frombuffer(chunk_bytes, dtype=dtype)

def plot_compare(filename, error_sample, translen, datasize, nchan, first_burst, atol=0):
    aligned_sample = (error_sample // translen) * translen
    burst_num = aligned_sample // translen
    
    max_channels_per_figure = 8
    bad_burst_array = read_chunk(filename, aligned_sample, translen, datasize, nchan)
    first_burst_channels = demux_burst(first_burst, nchan)
    bad_burst_channels = demux_burst(bad_burst_array, nchan)
    
    channels_with_errors = {}
    for ch_num in sorted(bad_burst_channels.keys()):
        diff = np.abs(bad_burst_channels[ch_num] - first_burst_channels[ch_num])
        exceeds_tolerance = diff > atol
        if np.any(exceeds_tolerance):
            error_indices = np.where(exceeds_tolerance)[0]
            channels_with_errors[ch_num] = error_indices
    
    sorted_error_channels = sorted(channels_with_errors.keys())
    num_error_channels = len(sorted_error_channels)
    num_figures = (num_error_channels + max_channels_per_figure - 1) // max_channels_per_figure
    
    figures = []
    for fig_idx in range(num_figures):
        start_ch = fig_idx * max_channels_per_figure
        end_ch = min(start_ch + max_channels_per_figure, num_error_channels)
        channels_in_figure = sorted_error_channels[start_ch:end_ch]
        num_ch_in_figure = len(channels_in_figure)
        
        fig, axes = plt.subplots(num_ch_in_figure, 1, figsize=(12, min(2 * num_ch_in_figure, 16)))
        if num_ch_in_figure == 1:
            axes = [axes]
        
        for idx, ch_num in enumerate(channels_in_figure):
            ax = axes[idx]
            bad_data = bad_burst_channels[ch_num]
            first_data = first_burst_channels[ch_num]
            error_indices = channels_with_errors[ch_num]
            
            ax.plot(
                bad_data,
                label=f'Bad Burst',
                linewidth=0.5,
                color='red',
                alpha=0.7
            )
            ax.plot(
                first_data,
                label='First Burst',
                linewidth=0.5,
                color='blue',
                alpha=0.7
            )
            
            if len(error_indices) > 0:
                ax.scatter(
                    error_indices,
                    bad_data[error_indices],
                    marker='v',
                    color='red',
                    s=50,
                    zorder=5,
                )
            
            ax.set_xlabel('Samples')
            ax.set_ylabel('Codes')
            ax.set_title(f'Channel {ch_num} (Errors: {len(error_indices)})')
            ax.legend()
        
        plt.suptitle(f'First Burst vs Burst #{burst_num}')
        plt.tight_layout()
        figures.append(fig)
    
    plt.show()

def plot_burst(filename, translen, datasize, nchan, burst_start, burst_end):

    if burst_start < 0 or burst_end < burst_start:
        raise ValueError("Error: burst range invalid")

    plot_start = burst_start * translen
    plot_end = (burst_end + 1) * translen
    num_samples = plot_end - plot_start
    title = f'Burst {burst_start} to {burst_end}'

    data_array = read_chunk(filename, plot_start, num_samples, datasize, nchan)
    channel_data = demux_burst(data_array, nchan)
    
    plt.figure(figsize=(16, 10))
    
    
    for ch_num in sorted(channel_data.keys()):
        plt.plot(
            channel_data[ch_num],
            label=f'Channel {ch_num}', 
            linewidth=0.5
        )
    
    plt.xlabel('Samples')
    plt.ylabel('Codes')
    plt.title(title, fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.show()

def demux_burst(data_array, nchan):
    num_samples_actual = len(data_array) // nchan
    data_reshaped = data_array[:num_samples_actual * nchan].reshape(num_samples_actual, nchan)
    
    channel_data = {}
    for ch in range(1, nchan + 1):
        channel_data[ch] = data_reshaped[:, ch - 1]
    
    return channel_data


def int_range(value):
    return list(map(int, value.split(':')))

def get_parser():
    parser = argparse.ArgumentParser(description='Check bursts')
    parser.add_argument('--file', required=True, help='file')
    parser.add_argument('--translen', required=True, type=int, help='translen')
    parser.add_argument('--nchan', type=int, required=True, help='nchan')
    parser.add_argument('--plot_bursts', type=int_range, default=None, help='Bursts to plot START:STOP')
    parser.add_argument('--tolerance', type=float, default=15, help='tolerance percent of max scale')
    parser.add_argument('--datasize', type=int, default=2, help='data size')
    parser.add_argument('--compare', action='store_true', help='compare bad burst to first burst')
    parser.add_argument('--rate', action='store_true', help='print the error rate instead of plotting the first error')
    parser.add_argument('--skip', type=int, default=0, help='skip first N bursts when checking')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
