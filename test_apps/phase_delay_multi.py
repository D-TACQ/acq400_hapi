#!/usr/bin/env python3

import os
import argparse
import numpy as np
from scipy.signal import hilbert, chirp
from prettytable import PrettyTable

#./phase_delay_multi.py --s_clk=20000 --fsig=20 --method=1 --type=32 BROTH/*

def run_comparison(args, method):
    files = args.files.copy()
    t = PrettyTable(['File1', 'File2', 'Diff(Nanoseconds)', 'Diff as % of sample clock'])
    while len(files) > 1:
        first = files.pop(0)
        for second in files:
            first_filename = os.path.basename(first)
            second_filename = os.path.basename(second)
            phase_diff, degrees, sec, percent = methods[method][1](args,first,second)
            t.add_row([first_filename, second_filename, sec, percent])
        t.add_row(["-", "-", "-", "-"]) # Empty row to demarcate first box in comparison
    title = "{} fsig: {} s_clk: {}".format(methods[method][0],args.fsig,args.s_clk)
    t.title = title
    print(t)
    if args.output:
        filename = "{}-{}.csv".format(args.output,title.replace(" ", "_"))
        with open(filename, 'w', newline='') as f_output:
            f_output.write(t.get_csv_string())

def common_calc(args, first, second):
    x1 = np.fromfile(first, dtype=args.type)
    x2 = np.fromfile(second, dtype=args.type)
    # Remove offsets
    x1 = x1 - np.mean(x1)
    x2 = x2 - np.mean(x2)
    # Scale x2 to match x1
    m1 = np.mean(abs(x1))
    x2 = x2 * (m1/np.mean(abs(x2)))
    # Difference
    y3 = (x2 - x1) / m1
    return x1, x2, m1

def taylor_series(args,first,second):
    x1, x2, m1  = common_calc(args,first,second)
    phase_diff = np.mean(abs(np.subtract(x2, x1)) / m1)
    return common_out(phase_diff,args)

def phase_sensitive_detector(args,first,second):
    x1, x2, m1  = common_calc(args,first,second)
    phase_diff = np.arccos(np.dot(x1, x2) / (np.linalg.norm(x1)*np.linalg.norm(x2)))
    return common_out(phase_diff,args)

def fast_fourier_transform(args,first,second):
    exit("method broke")
    x1, x2, m1  = common_calc(args,first,second)
    fft_x1 = np.fft.fft(x1)
    fft_x2 = np.fft.fft(x2)
    #print "ffts = ", fft_x1, fft_x2
    l1 = len(fft_x1)
    l2 = len(fft_x2)
    phase_diff = np.angle(fft_x1[0:(l1+1/2)] / fft_x2[0:l2+1/2]) #slices array by float?
    phase_diff = float(np.pi) - float(phase_diff[0])
    return common_out(phase_diff,args)

def hilbert_transform(args, first, second):
    x1, x2, m1  = common_calc(args, first, second)
    x1h = hilbert(x1)
    x2h = hilbert(x2)
    ph_diff = np.angle(x1h / x2h)
    phase_diff = abs(ph_diff[0])
    return common_out(phase_diff, args)

def common_out(phase_diff, args):
    degrees = phase_diff * (1/(np.pi / 180))
    sec = degrees / (360 * args.fsig)
    percent = sec * 100 * args.s_clk
    ex = 10 ** 9
    return  round(phase_diff, 2), round(degrees, 2), round(sec * ex, 2), round(percent, 2)

def run_main(args):
    args.type = np.int16 if args.type == 16 else np.int32
    if len(args.files) < 2:
        exit("More than 2 files required")
    methods = args.method.split(',')
    for method in methods:
        run_comparison(args, int(method))

def get_parser():
    method_help = ""
    for k, v in sorted(methods.items()):
        method_help += "{}: {} ".format(k,v[0])

    parser = argparse.ArgumentParser(description='Checks phase delay')
    parser.add_argument('--fsig', type=int, default=488, help='Frequency of the signal.', required=True)
    parser.add_argument('--s_clk', type=int, default=48800, help='Frequency of the clk.', required=True)
    parser.add_argument('--method', default="1", help=method_help)
    parser.add_argument('--type', type=int, default=16, help='16 or 32 bit data')
    parser.add_argument('--output', type=str, default=None, help='cvs filename to write to')
    parser.add_argument('files', help='Files to process', nargs='+')
    return parser

methods = {
    1: ( "Taylor Series", taylor_series ),
    2: ("Phase Sensitive Detector", phase_sensitive_detector),
    3: ("Fast Fourier Transform", fast_fourier_transform),
    4: ("Hilbert Transform", hilbert_transform)
}

if __name__ == '__main__':
    run_main(get_parser().parse_args())
