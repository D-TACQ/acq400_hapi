#!/usr/bin/python


import epics
import time
import argparse
import matplotlib.pyplot as plt
import numpy as np

time_stamp = time.time()
times = []
epics_times = []


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='PyEPICS burst monitor')
    parser.add_argument('uut', nargs='+', help="uut")
    return parser.parse_args(argStr)


def cb_function(pvname=None, value=None, char_value=None, timestamp=None, **kw):
    global time_stamp
    global times
    global epics_times
    current_time = time.time()
    diff = current_time - time_stamp
    times.append(diff)
    epics_times.append(timestamp)
    time_stamp = current_time
    return None


def main():
    args = get_args()
    pv = epics.PV('{}:JDG:CHX:FAIL:ALL'.format(args.uut[0])) #, callback=cb_function))
    pv.add_callback(cb_function)
    #epics.camonitor('{}:JDG:CHX:FAIL:ALL'.format(args.uut[0], callback=cb_function))
    time.sleep(30)
    print("Done")
    
    plt.hist(times)

    epics_times_diff = np.diff(epics_times)
    plt.show()
    plt.hist(epics_times_diff)
    plt.show()

if __name__ == '__main__':
    main()
