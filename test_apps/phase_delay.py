#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import argparse
from scipy.signal import hilbert, chirp

def run_test(args):

    # Load files
    ch1 = np.fromfile(args.file1, dtype=np.int16)
    ch2 = np.fromfile(args.file2, dtype=np.int16)

    x1 = ch1
    x2 = ch2

    # Remove offsets
    x1 = x1 - np.mean(x1);
    x2 = x2 - np.mean(x2);

    # Scale x2 to match x1
    m1 = np.mean(abs(x1))
    x2 = x2 * (m1/np.mean(abs(x2)))

    #Difference
    y3 = (x2 - x1) / m1

    if args.method == 1:
        # Using 'Taylor Series' method
        phase_diff = np.mean(abs(np.subtract(x2,x1)) / m1)

    elif args.method == 2:
        # Using phase sensitive detector
        phase_diff = np.arccos( np.dot(x1,x2) / (np.linalg.norm(x1)*np.linalg.norm(x2)) )

    elif args.method == 3:
        # FFT method
        fft_x1 = np.fft.fft(x1)
        fft_x2 = np.fft.fft(x2)
        print "ffts = ", fft_x1, fft_x2
        l1 = len(fft_x1)
        l2 = len(fft_x2)
        phase_diff = np.angle(fft_x1[0:l1+1/2] / fft_x2[0:l2+1/2])
        phase_diff = float(np.pi) - float(phase_diff[0])

    elif args.method == 4:
        # Hilbert transform method
        x1h = hilbert(x1)
        x2h = hilbert(x2)
        ph_diff = np.angle(x1h/x2h)
        phase_diff = ph_diff[0]

    print "Phase difference in rads = ", phase_diff

def run_main():
    parser = argparse.ArgumentParser(description = 'awg speed test')
    parser.add_argument('--file1', type=str, default="CH01", help='ch1 file name')
    parser.add_argument('--file2', type=str, default="CH02", help='ch2 file name')
    parser.add_argument('--method', type=int, default=1, help='Which method to use.')
    run_test(parser.parse_args())


if __name__ == '__main__':
    run_main()
