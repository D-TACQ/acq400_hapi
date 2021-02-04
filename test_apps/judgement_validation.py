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

    parser.add_argument('--validation', type=int, default=1,
                        help="validation type - 1: Use default 3 sine wave "
                        "burst, 2: Use first buffer as validator +- threshold")

    parser.add_argument('--es_indices', type=str, default="0,1024",
                        help="Locations of event samples in the data separated"
                        " by commas. For example: --es_indices='0,1024'")

    parser.add_argument('--stdin', type=int, default=1,
                        help='Whether to load data from STDIN or from '
                        'acq400_hapi. Default is STDIN.')

    parser.add_argument('uut', nargs=1, help="uut")
    args = parser.parse_args()
    return args


def check_channel(channel, validation):
    check_upper = validation[0][1:] - channel[1:]
    check_lower = channel[1:] - validation[1][1:]
    if (check_upper < 0).any() or (check_lower < 0).any():
        return True
    return False


def generate_boundary(validation, nchan, bufferlen, threshold, es_indices, stdin, data=[]):
    if validation == 1:
        x = np.linspace(0, 6*np.pi, 750)
        y = 3000 * np.sin(x)
        y2 = np.concatenate((y, np.zeros(274)))
        y3 = np.concatenate((y2, y2))
        y3[es_indices] = np.nan
        data = [y3] * nchan
        validation_data = [[ch + threshold, ch - threshold] for ch in data]
        return validation_data

    elif validation == 2:
        if stdin:
            raw_data = sys.stdin.buffer.read(bufferlen)
            raw_data = np.fromstring(raw_data, dtype=np.int16)

        else:
            raw_data = np.frombuffer(data, dtype=np.int16)
            print("raw_data shape: {}".format(raw_data.shape))
        data = raw_data.reshape((-1, nchan)).T
        data = data.astype(np.float)

        for num, channel in enumerate(data):
            data[num][es_indices] = np.nan
        validation_data = [[ch + threshold, ch - threshold] for ch in data]

        return validation_data


def generate_fail_report(data, validation_data):
    fail_report = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(check_channel, data, validation_data)
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
    data.tofile(file_name)
    return None


def main():
    args = get_args()
    uut = args.uut[0]

    file_name = "./{}/{}"
    make_data_dir(uut, 0)

    buffer_num = 0
    uut_object = acq400_hapi.Acq400(uut)
    nchan = uut_object.nchan()
    bufferlen = int(uut_object.s0.bufferlen)
    es_indices = [int(num) for num in args.es_indices.split(",")]

    if args.stdin == 1:

        validation_data = generate_boundary(args.validation, nchan, bufferlen,
                                            args.threshold, es_indices,
                                            args.stdin)

        while True:

            buffer_num += 1
            file_name = "./{}/{:05d}".format(uut, buffer_num)

            if args.stdin == 1:
                raw_data = sys.stdin.buffer.read(bufferlen)
                raw_data = np.fromstring(raw_data, dtype=np.int16)
                data = raw_data.reshape((-1, nchan)).T

            compare_epics_python(args, raw_data, data, validation_data, uut, file_name)

    else:
        collect_validation = True
        for bytedata in uut_object.stream(recvlen=bufferlen):
            if collect_validation:
                validation_data = generate_boundary(args.validation, nchan, bufferlen,
                                                    args.threshold, es_indices,
                                                    args.stdin, data=bytedata)
            raw_data = np.frombuffer(bytedata, dtype=np.int16)
            data = raw_data.reshape((-1, nchan)).T

            compare_epics_python(args, raw_data, data, validation_data, uut, file_name)
            collect_validation = False
    return None


def compare_epics_python(args, raw_data, data, validation_data, uut, file_name):
    fail_list = np.array(generate_fail_report(data, validation_data))
    pv_check = np.array(epics.caget('{}:JDG:CHX:FAIL:ALL'.format(uut)))[1:]

    if fail_list.any() or pv_check.any():
        print("Judgement fail detected! {}".format(
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        if args.save_data == 1:
            save_data(raw_data, file_name + "_failed_judgement")

    if not np.array_equal(pv_check, fail_list):
        print("PV does not agree with numpy.")
        print("True, or 1 means judgement fired (error detected)")
        print("PV: {}".format(pv_check))
        print("PY: {}".format(fail_list))
        print("Channels where PV == PY:")
        print(pv_check == fail_list)

    if args.save_data == 2:
        save_data(data, file_name)
    return None


if __name__ == '__main__':
    main()
