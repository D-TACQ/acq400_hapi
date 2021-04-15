#!/usr/bin/python

import epics
import argparse
import acq400_hapi
import numpy as np


def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')
    parser.add_argument('uut', nargs=1, help="uut ")
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    uut = args.uut[0]
    uut_object = acq400_hapi.Acq400(uut)
    nchan_site = int(uut_object.s1.NCHAN)

    x = np.linspace(0, 6*np.pi, 750)
    y = np.sin(x)
    y2 = np.concatenate((y, np.zeros(274)))

    upper = y2 + 1
    lower = y2 - 1

    for chan in range(1, nchan_site+1):
        pv = epics.PV('{}:1:JDG:MU:{:02d}:V'.format(uut, chan))
        pv.put(upper)
        pv = epics.PV('{}:1:JDG:ML:{:02d}:V'.format(uut, chan))
        pv.put(lower)
        print("Finished site 1 CH{}".format(chan))

    for chan in range(1, nchan_site+1):
        pv = epics.PV('{}:2:JDG:MU:{:02d}:V'.format(uut, chan))
        pv.put(upper)
        pv = epics.PV('{}:2:JDG:ML:{:02d}:V'.format(uut, chan))
        pv.put(lower)
        print("Finished site 2 CH{}".format(chan))

    return None


if __name__ == '__main__':
    main()
