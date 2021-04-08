#!/usr/bin/python3

import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys


def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')
    parser.add_argument('--file', type=str, default="ansto_file.dat", help="File to load.")
    args = parser.parse_args()
    return args


def compare_bursts(first_burst, burst_n):
    first_burst = np.array(first_burst)
    burst_n = np.array(burst_n)

    if len(first_burst) > len(burst_n):
        first_burst = first_burst[0:len(burst_n)]
    elif len(burst_n) > len(first_burst):
        burst_n = burst_n[0:len(first_burst)]

    if np.allclose(burst_n, first_burst, rtol=0, atol=15000000):
        # plt.plot(first_burst)
        # plt.plot(burst_n)
        # plt.plot(np.abs(first_burst - burst_n))
        # plt.show()
        return True
    else:
        print(first_burst)
        print(burst_n)
        plt.plot(first_burst)
        plt.plot(burst_n)
        plt.plot(np.abs(first_burst - burst_n))
        plt.show()
        return False


def main():
    args = get_args()
    NCHAN = 10
    data = np.fromfile(args.file, dtype=np.int32)

    # reshape
    data = data.reshape((-1, NCHAN))
    CH01 = data[0:,0]
    timbus = data[0:,8]
    # plt.plot(CH01)
    # plt.plot(timbus)
    # plt.grid(1)
    # plt.show()
    #test = np.where(data[8] ,a, 1)

    mask = np.argwhere(np.bitwise_and(timbus, 0x10000000))
    # print(CH01[mask])
    test_plot = CH01[mask]
    # plt.plot(test_plot)
    # plt.grid(1)
    # plt.show()
    data = data[15:]
    init = [0, 0]  # (had a zero before, had a 1 before)
    first_burst = []
    burst_n = []
    for num, row in enumerate(data):
        # if num < 15:
        #     continue
        if np.bitwise_and(row[8], 0x10000000):
            if init[0] == 0:
                first_burst.append(row[0])
                init[1] = 1
            else:
                burst_n.append(row[0])
                init = [2, 1]

            continue
        else:

            if init[1] == 1:
                if init[0] == 0:
                    init[0] = 1
            if init == [2, 1]:
                if not compare_bursts(first_burst, burst_n):
                    print("Problem detected in burst. Quitting now.")
                    sys.exit(1)
                else:
                    print("No issues found...{}".format(num))
                burst_n = []
                init = [2, 0]

    return None


if __name__ == '__main__':
    main()
