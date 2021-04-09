#!/usr/bin/python3
'''
extract signal burst information from stream data.

The data set includes: 8 channel AI, 32bit DI data from "TIMBUS" and a sample count

data format:
int32 AI[8]
uint32 DI       
uint32 SCOUNT

DI is current DI state aligned with AI data. 
TRG INPUT is connected to bit 28

AI data is a 24 bit value left justified in a 32 bit field..
'''


import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys


NCHAN = (8+1+1)               # 8AI, DI32, COUNT in longwords
TRG_DI = 0x10000000           # trigger input appears here in 32b mask

TOLERANCE = 0.005              # 0.5% error target

# +10V=0x7fffffff
def volts2raw(v):
    return int(v*(0x7fffff00/10))

RAW_TOL = volts2raw(TOLERANCE*10)
print(RAW_TOL)

def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')
    parser.add_argument('--file', type=str, default="ansto_file.dat", help="File to load.")
    parser.add_argument('--skip', type=int, default=15, help="")
    parser.add_argument('--plot', type=int, default=0, 
            help="0: no plot, 1: plot raw, 2:plot gated, 4 plot first burst")

    args = parser.parse_args()
    return args

PLOT_RAW   = 1
PLOT_GATED = 2
PLOT_FIRST = 4

# index to data
IDX_CH01 = 0
IDX_DI32 = 8

def compare_bursts(args, burst_0, burst_n):
    burst_0 = np.array(burst_0)
    burst_n = np.array(burst_n)

    if len(burst_0) > len(burst_n):
        burst_0 = burst_0[0:len(burst_n)]
    elif len(burst_n) > len(burst_0):
        burst_n = burst_n[0:len(burst_0)]

    if np.allclose(burst_n, burst_0, rtol=0, atol=RAW_TOL):
        if args.plot&PLOT_FIRST:
            plt.plot(burst_0)
            plt.plot(burst_n)
            plt.plot(np.abs(burst_0 - burst_n))
            plt.suptitle("Single Burst")
            plt.show()
            args.plot = 0
        return True
    else:
        print(burst_0)
        print(burst_n)
        plt.plot(burst_0)
        plt.plot(burst_n)
        plt.plot(np.abs(burst_0 - burst_n))
        plt.show()
        return False


def main():
    args = get_args()
    data = np.fromfile(args.file, dtype=np.int32)

    # data shape [NSAMPLES..HUGE][NCHAN=10]
    data = data.reshape((-1, NCHAN))
    CH01 = data[0:,IDX_CH01]
    timbus = data[0:,IDX_DI32]
    if args.plot& PLOT_RAW:
        plt.plot(CH01)
        plt.plot(timbus)
        plt.suptitle("Raw Plot")
        plt.grid(1)
        plt.show()

    mask = np.argwhere(np.bitwise_and(timbus, TRG_DI))
    if args.plot&PLOT_GATED:
        test_plot = CH01[mask]
        plt.plot(test_plot)
        plt.suptitle("Gated Plot")
        plt.grid(1)
        plt.show()

    data = data[args.skip:]
    init = [0, 0]  # (had a zero before, had a 1 before)
    burst_0 = []
    burst_n = []
    burst = 0
    for sample, row in enumerate(data):
        if np.bitwise_and(row[IDX_DI32], TRG_DI):
            if init[0] == 0:
                burst_0.append(row[IDX_CH01])
                init[1] = 1
            else:
                burst_n.append(row[IDX_CH01])
                init = [2, 1]

            continue
        else:

            if init[1] == 1:
                if init[0] == 0:
                    init[0] = 1
            if init == [2, 1]:
                if not compare_bursts(args, burst_0, burst_n):
                    print("Problem detected in burst {}. Quitting now.".format(burst))
                    sys.exit(1)
                else:
                    print("Sample {} .. No issues found".format(sample))
                burst_n = []
                burst += 1
                init = [2, 0]

    print("Processed {} samples and {} bursts".format(sample, burst))
    return None


if __name__ == '__main__':
    main()
