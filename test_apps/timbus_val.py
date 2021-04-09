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

def raw2volts(r):
    return 10.0*r/0x7fffff00

RAW_TOL = volts2raw(TOLERANCE*10)
print(RAW_TOL)

def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')
    parser.add_argument('--file', type=str, default="ansto_file.dat", help="File to load.")
    parser.add_argument('--skip', type=int, default=15, help="")
    parser.add_argument('--plot', type=int, default=0, 
            help="0: no plot, OR of 1: plot raw, 2:plot gated, 4 plot first burst, 8 plot delta.")
    parser.add_argument('--verbose', type=int, default=0)

    args = parser.parse_args()
    return args

PLOT_RAW   = 1
PLOT_GATED = 2
PLOT_FIRST = 4
PLOT_DELTA = 8

# index to data
IDX_CH01 = 0
IDX_DI32 = 8

'''
First 10 samples see the soft trigger .. 
[pgm@hoy5 acq400_hapi]$ hexdump -e '10/4 "%08x," "\n"' /home/pgm/D-Tacq/Customer/ANSTO/ansto_file2.dat | head -n 12
0934dd20,00076121,0000c822,00051323,fffd4224,fffdb425,00012c26,00001d27,33000000,00000001,
08958d20,00075421,00008722,00050623,fffd6b24,fffd7525,00012326,00006027,33000000,00000002,
07f75620,00072b21,00009022,0004fc23,fffd9124,fffd9925,00012e26,00003b27,33000000,00000003,
07598d20,00079f21,0000d122,00057623,fffd4624,fffd5d25,0000ff26,00002727,33000000,00000004,
06ba7720,00075c21,0000b822,00050123,fffd7e24,fffd8725,00012626,00002e27,33000000,00000005,
061bcd20,00074921,0000c922,00052123,fffd8724,fffd9c25,00015326,00003e27,33000000,00000006,
057d6b20,00075421,0000a522,00051f23,fffd6e24,fffda425,00010e26,00000f27,33000000,00000007,
04de8620,00076321,0000a222,00052523,fffd4d24,fffd5b25,00014d26,00007227,33000000,00000008,
043ecf20,00076c21,0000f322,00055e23,fffd4a24,fffd9525,00013f26,00002527,11000000,00000009,
03a05d20,00077421,0000ad22,00051e23,fffd7d24,fffd6125,00014a26,00004a27,11000000,0000000a,
0301c720,00075821,0000bf22,00052623,fffdb524,fffda025,00014e26,00002827,11000000,0000000b,
'''

def compare_bursts(args, burst_0, burst_n, burst):
    if len(burst_0) > len(burst_n):
        burst_0 = burst_0[0:len(burst_n)]
    elif len(burst_n) > len(burst_0):
        burst_n = burst_n[0:len(burst_0)]

    if np.allclose(burst_n, burst_0, rtol=0, atol=RAW_TOL):
        if args.plot&PLOT_FIRST:
            plt.plot(raw2volts(burst_0))
            plt.plot(raw2volts(burst_n)+1.0)
            plt.ylabel("Volts")
            plt.suptitle("Single Burst offset 1V vs model ")
            plt.show()
            args.plot = 0
        if args.plot&PLOT_DELTA:
            plt.plot(raw2volts(np.abs(burst_0 - burst_n)))
            plt.ylabel("Volts")
            plt.suptitle("Single Burst {} error vs model".format(burst))
            plt.show()
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
    CH01 = data[:,IDX_CH01]
    timbus = np.bitwise_and(data[:,IDX_DI32], TRG_DI)

    if args.plot& PLOT_RAW:
        plt.plot(raw2volts(CH01))
        plt.plot(raw2volts(timbus)*4)      # timbus is bit 28
        plt.suptitle("Raw Plot")
        plt.ylabel("Volts")
        plt.grid(1)
        plt.show()

    mask = np.argwhere(np.bitwise_and(timbus, TRG_DI))
    if args.plot&PLOT_GATED:
        test_plot = CH01[mask]
        plt.plot(raw2volts(test_plot))
        plt.ylabel("Volts")
        plt.suptitle("Gated Plot")
        plt.grid(1)
        plt.show()

    data = data[args.skip:]
    burst_0 = []                          # first (reference) burst
    burst_n = []                          # current burst
    burst = 0                             # burst number
    in_burst = False
    good = False
    burst_x = burst_0                     # fill cursor
    for sample, row in enumerate(data):
        if np.bitwise_and(row[IDX_DI32], TRG_DI):
            in_burst = True
            burst_x.append(row[IDX_CH01])
        else:
            if in_burst:
                in_burst = False
                if burst_x == burst_0:
                    burst_x = burst_n
                else:
                    good = compare_bursts(args, np.array(burst_0), np.array(burst_n), burst)
                    if (args.verbose):
                        print("Sample {} Burst {} Status {}".format(sample, burst, "PASS" if good else "FAIL"))
                    if good:
                        burst_n.clear()
                        burst += 1
                    else:
                        sys.exit(1)

    print("Processed {} samples and {} bursts {}".format(sample, burst, "PASS" if good else "FAIL"))
    return None


if __name__ == '__main__':
    main()
