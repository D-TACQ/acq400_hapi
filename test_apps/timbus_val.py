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

[peter@andros NEC2.2]$ python3 ~/PROJECTS/acq400_hapi/test_apps/timbus_val.py --help
usage: timbus_val.py [-h] [--aichan AICHAN] [--pchan PCHAN] [--nspad NSPAD]
                     [--file FILE] [--skip SKIP] [--plot PLOT]
                     [--verbose VERBOSE]

analyse stored data with TIMBUS

optional arguments:
  -h, --help         show this help message and exit
  --aichan AICHAN
  --pchan PCHAN      plot this channel
  --nspad NSPAD
  --file FILE        File to load.
  --skip SKIP
  --plot PLOT        0: no plot, OR of 1: plot raw, 2:plot gated, 4 plot first
                     burst, 8 plot delta.

NEC example
 python3 ~/PROJECTS/acq400_hapi/test_apps/timbus_val.py --file big5 --verbose=1 --aichan=24 --nspad=4 --pchan=5 --plot=1
'''


import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys

AICHAN = 8                    # ANSTO
#AICHAN=24                     # NEC	--aichan=24
NCHAN = (AICHAN+1+1)               # 8AI, DI32, COUNT in longwords
#NCHAN = (AICHAN+1+4)               # 8AI, DI32, COUNT in longwords
TRG_DI = 0x10000000           # trigger input appears here in 32b mask
TRG_DI_SCALE = 4              # convert bit mask to half scale (aka 5V)

TOLERANCE = 0.005              # 0.5% error target

# +10V=0x7fffffff
def volts2raw(v):
    return int(v*(0x7fffff00/10))

def raw2volts(r):
    return 10.0*r/0x7fffff00

RAW_TOL = volts2raw(TOLERANCE*10)
#print(RAW_TOL)

def get_args():
    global AICHAN, NCHAN
    parser = argparse.ArgumentParser(description='analyse stored data with TIMBUS')
    parser.add_argument('--aichan', type=int, default=8 )
    parser.add_argument('--pchan', type=int, default=1, help="plot this channel")
    parser.add_argument('--nspad',  type=int, default=1)
    parser.add_argument('--file', type=str, default="ansto_file.dat", help="File to load.")
    parser.add_argument('--skip', type=int, default=0, help="")
    parser.add_argument('--plot', type=int, default=0, 
            help="0: no plot, OR of 1: plot raw, 2:plot gated, 4 plot first burst, 8 plot delta.")
    parser.add_argument('--verbose', type=int, default=0)
    args = parser.parse_args()

    AICHAN = args.aichan
    NCHAN = args.aichan + 1 + args.nspad
    return args

PLOT_RAW   = 1
PLOT_GATED = 2
PLOT_FIRST = 4
PLOT_DELTA = 8

'''
First 10 samples see the soft trigger .. 
First burst is short (happened to catch the signal on a high .. discarded)
[pgm@hoy5 acq400_hapi]$ hexdump -e '10/4 "%08x," "\n"' /home/pgm/D-Tacq/Customer/ANSTO/ansto_file2.dat | head -n 12
    AI01,    AI02,    AI03,    AI04,    AI05,    AI06,    AI07,    AI08,    DI32,   COUNT
                                                                        22000000 :: TRG.d1 SOFT TRIGGER 
                                                                        11000000 :: TRG.d0 FP TRIGGER
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

# transition to burst in-shot..
....
fd99cd20,00035921,fffeef22,00039e23,fffd4524,fffd8925,00015e26,00009f27,00000000,0000028c,
fe381920,00031b21,fffed122,0003aa23,fffd2024,fffdb125,00010e26,0000a127,00000000,0000028d,
fed7ba20,00032f21,fffec622,0003da23,fffd4c24,fffd4e25,00012426,0000e927,00000000,0000028e,
ff775820,00033e21,fffeb422,0003e023,fffd5d24,fffdc325,00018a26,00007c27,11000000,0000028f,
0015f220,00033d21,fffeba22,0003b223,fffd4a24,fffda225,00010626,00008127,11000000,00000290,
00b4fa20,00033421,fffecc22,0003c223,fffd4e24,fffd9625,0000fd26,00009027,11000000,00000291,

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
        plt.plot(np.abs(burst_0 - burst_n))
        plt.ylabel("Volts")
        plt.suptitle("Single Burst {} error vs model ERROR OUT OF TOLERANCE".format(burst))
        plt.show()
        return False


def main():
    args = get_args()
    data = np.fromfile(args.file, dtype=np.int32)

    # data shape [NSAMPLES..HUGE][NCHAN=10]
    data = data.reshape((-1, NCHAN))
    ch01 = data[:,args.pchan-1]
    dix = np.bitwise_and(data[:,args.aichan], TRG_DI)
    mask = np.argwhere(dix)

    if args.plot& PLOT_RAW:
        plt.plot(raw2volts(ch01))
        plt.plot(raw2volts(dix)*TRG_DI_SCALE)
        plt.suptitle("Raw Plot")
        plt.ylabel("Volts")
        plt.grid(1)
        plt.show()
    
    if args.plot&PLOT_GATED:
        plt.plot(raw2volts(ch01[mask]))
        plt.ylabel("Volts")
        plt.suptitle("Gated Plot")
        plt.grid(1)
        plt.show()


    data = data[args.skip:]
    burst_0 = []                          # first (reference) burst
    burst_n = []                          # current burst
    burst = 0                             # burst number
    has_been_low = False                  # must see a low BEFORE we start, initial high may be invalid
    in_burst = False                      # set when we have a HI and previously we have seen a low
    good = False
    burst_x = burst_0                     # fill cursor

    for sample, row in enumerate(data):
        if np.bitwise_and(row[IDX_DI32], TRG_DI):
            if has_been_low:
                in_burst = True
                burst_x.append(row[IDX_CH01])
        else:
            has_been_low = True
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
                        break

    print("Processed {} samples and {} bursts {}".format(sample, burst, "PASS" if good else "FAIL"))
    return None


if __name__ == '__main__':
    main()
