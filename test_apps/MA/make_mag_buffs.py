#!/usr/bin/env python


import numpy as np
import argparse


def load_wf(args):
    data = np.fromfile(args.datafile, dtype=np.int16)
    return data


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def extend_to_16_ch(args, data):
    # Assuming only 4 channels
    data_size = len(data) * 2
    data2 = [[],[],[],[]]
    data_chunks = chunks(data, len(data)/4) # split list into 4 chunks
    print "dchunks = ", data_chunks
    for num, chunk in enumerate(data_chunks):
        # data2 = data[0:len(data)/8]
        # for index, element in enumerate(data[0::4]):
        for index in range(0,len(chunk),4):
            for xx in range(0, 5): # For each element do this 4 times.
                data2[num].append(chunk[index])
                data2[num].append(chunk[index+1])
                if xx == 4:
                    data2[num].append(chunk[index+2])
                    data2[num].append(data[index+3])
                    for yy in range(0, 4):
                        data2[num].append(-5000)

    return data2


def extend_to_n_bytes(args, data):
    final_data = []
    for index, buf in enumerate(data):
        data_size = len(buf) * 2 # Data size in bytes
        print "len(buf) = ", len(buf)
        samples_needed = (args.size - data_size) / 2 # samples reqd to pad to 1MB buffers
        print "samples needed = ", samples_needed
        chunk = np.append(buf, samples_needed * [0]) # data is 1MB
        final_data.append(chunk)
        print "data shape ", np.shape(final_data)
    final_data = np.array(final_data).astype(np.int16)
    print "data = ", np.shape(final_data)
    return final_data


def export_data(args, data):
    np.ndarray.tofile(data, args.out)
    return None


def make_buff(args):
    data = load_wf(args)
    data = extend_to_16_ch(args, data)
    data = extend_to_n_bytes(args, data)
    export_data(args, data)

    data = load_wf(args)
    data = extend_to_16_ch(args, data)
    data = extend_to_n_bytes(args, data)
    export_data(args, data)
    return None


def run_main():
    parser = argparse.ArgumentParser(description = 'make magarray buffers.')
    parser.add_argument('--datafile', type=str, default="awgdata.dat",
    help="Which datafile to load.")
    parser.add_argument('--out', type=str, default="4mb_sines.dat",
    help='The name of the output file')
    parser.add_argument('--size', type=int, default=1048576,
    help='Size in bytes of the buffer size required.')
    args = parser.parse_args()
    make_buff(args)


if __name__ == '__main__':
    run_main()
