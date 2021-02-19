#!/usr/bin/python3

import argparse
import epics
import time
import os


def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')

    parser.add_argument('--post', type=int, default=100000, help="POST trigger samples to capture. Default=100,000")
    parser.add_argument('--trg', type=str, default='int', help="Trigger, either 'int' or 'ext'. Default='int'")
    parser.add_argument('--shots', type=int, default=1, help="Number of shots to run. Default=1")

    parser.add_argument('uuts', nargs='+', help="uut")
    args = parser.parse_args()
    return args

def offload_data(uut, shot_number, post):
    directory = "{}/{:05d}".format(uut, shot_number)
    make_data_dir(directory, 0)
    for site in range(1, 4):
        for chan in range(1, 33):
            data = epics.caget("{}:1:AI:TW:{:02d}:V.VALA".format(uut, chan))
            data[0:post].tofile("{}/S{}_CH{:03d}.dat".format(directory, site, chan))
    return None


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


def main():
    global cb_counter
    args = get_args()
    uut = args.uuts[0]
    trg = 'd1' if args.trg == 'int' else 'd0'

    epics.PV('{}:MODE:TRANSIENT:PRE'.format(uut)).put(0)
    epics.PV('{}:MODE:TRANSIENT:POST'.format(uut)).put(args.post)
    epics.PV('{}:MODE:TRANSIENT'.format(uut)).put(1)
    epics.PV('{}:1:TRG:DX'.format(uut)).put(trg)

    shot_counter = 0

    while shot_counter < args.shots:
        print("Shot: {} starting now.".format(shot_counter))
        epics.PV('{}:MODE:TRANSIENT:SET_ARM'.format(uut)).put(1)

        while epics.PV('{}:MODE:TRANS_ACT:STATE'.format(uut)).get() != 0:
            print("state")
            time.sleep(0.5)

        offload_data(uut, shot_counter, args.post)
        shot_counter += 1

    print("returning now");
    return None

if __name__ == '__main__':
    main()
