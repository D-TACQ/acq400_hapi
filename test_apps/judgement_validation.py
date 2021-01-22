#!/usr/bin/python


import concurrent.futures
import acq400_hapi
import numpy as np
import datetime
import argparse
import epics
import sys
import os


def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')

    parser.add_argument('--save_data', type=int, default=0,
                        help="Save data to disk. Default: 0 (Don't save data),"
                        " 1: (Save only fails), 2: (Save every buffer)")

    parser.add_argument('--threshold', type=int, default=1000,
                        help="How close to ideal the judgement criteria are.")

    parser.add_argument('uut', nargs=1, help="uut ")
    args = parser.parse_args()
    return args


def check_channel(channel):
    global upper
    global lower
    check_upper = upper - channel
    check_lower = channel - lower
    if (check_upper < 0).any() or (check_lower < 0).any():
        return True
    return False


def generate_boundary():
    x = np.linspace(0, 6*np.pi, 750)
    y = 3000 * np.sin(x)
    y2 = np.concatenate((y, np.zeros(274)))
    y3 = np.concatenate((y2, y2))
    y3[0] = np.nan
    y3[1024] = np.nan
    return y3


def generate_fail_report(data):
    fail_report = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(check_channel, data)
        for result in results:
            fail_report.append(result)
    return fail_report


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


def save_data(data, file_name):
    # print("Saving judgement failed buffer to file: {}".format(file_name))
    data.tofile(file_name)
    return None


def main():
    args = get_args()
    uut = args.uut[0]

    file_name = "./{}/{}"
    make_data_dir(uut, 0)

    global upper
    global lower

    buffer_num = 0
    uut_object = acq400_hapi.Acq400(uut)
    nchan = uut_object.nchan()
    bufferlen = int(uut_object.s0.bufferlen)

    y = generate_boundary()

    upper = y + args.threshold
    lower = y - args.threshold

    while True:

        fail_list = []
        buffer_num += 1
        file_name = "./{}/{:05d}".format(uut, buffer_num)

        raw_data = sys.stdin.read(bufferlen)
        raw_data = np.fromstring(raw_data, dtype=np.int16)
        data = raw_data.reshape((-1, nchan)).T

        fail_list = np.array(generate_fail_report(data))
        pv_check = np.array(epics.caget('{}:JDG:CHX:FAIL:ALL'.format(uut)))[1:]

        if fail_list.any() or pv_check.any():
            print("Judgement fail detected! {}".format(
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            if args.save_data == 1:
                save_data(data, file_name + "_failed_judgement")

        if not np.array_equal(pv_check, fail_list):
            print("PV does not agree with numpy.")
            print("True, or 1 means judgement fired (error detected)")
            print("PV: {}".format(pv_check))
            print("NP: {}".format(fail_list))
            print("Channels that disagree:")
            print(pv_check == fail_list)

        if args.save_data == 2:
            save_data(data, file_name)

    return None


if __name__ == '__main__':
    main()
