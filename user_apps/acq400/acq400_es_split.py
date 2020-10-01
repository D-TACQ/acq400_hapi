#!/usr/bin/env python

import acq400_hapi
import numpy as np
import os
import argparse


def check_if_es(data):
    es_match = np.uint32(0xaa55f150)
    np_data = np.frombuffer(data, dtype=np.uint32)
    for es in np_data[0:4]:
        if es_match == np.bitwise_and(es, es_match):

            continue
        else:
            return False
    return True


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='acq400 upload')
    parser.add_argument('--file', default="./0000", type=str,
                        help='Which file to load to split on event signatures. Default=./0000')
    parser.add_argument('--ssb', default=-1, type=int,
                        help='Sample size bytes. Default=-1 (autodetect). Any other number is override.')
    parser.add_argument('--out_dir', default="./split_files", type=str,
                        help='Directory where split files will be written. Default: ./split_files')
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    return parser.parse_args(argStr)


def make_data_dir(directory, verbose):
    try:
        os.makedirs(directory)
    except Exception:
        if verbose:
            print("Tried to create dir but dir already exists")
        pass


def split_on_es(file, ssb, out_dir):
    data = [0]
    new_file_flag = True
    data_file = None
    file_num = 0
    make_data_dir(out_dir, 0)
    loop = 0

    with open(file, 'rb') as fp:
        while len(data) != 0:
            data = fp.read(ssb)
            if len(data) == 0:
                continue
            new_file_flag = check_if_es(data)

            if new_file_flag and loop != 0:
                file_num += 1
                data_file.close()
                data_file = None
                new_file_flag = False

            if data_file == None:
                data_file = open("{}/{:04d}".format(out_dir, file_num), "wb")

            data_file.write(data)
            loop += 1


def get_ssb(uut, ssb):
    if ssb == -1:
        uut = acq400_hapi.Acq400(uut)
        ssb = int(uut.s0.ssb)
    return ssb


def main():
    args = get_args()
    ssb = get_ssb(args.uuts[0], args.ssb)
    split_on_es(args.file, ssb, args.out_dir)
    return None


if __name__ == '__main__':
    main()
