#!/usr/bin/env python
# convert MA1 AWG file to MA2
# NSAMPLES x 4CH x 2BYTE raw file to
# NSAMPLES x "16CH" x 2BYTES, in 4 x 1MB chunks


import numpy as np
import argparse

INCHAN = 4                  # channels in source file

# Valid 4xACQ436, 1xAO420
OUTPAIRS = 4
OUTQUADS = 1

# Valid 5xACQ436, 1xAO420
#OUTPAIRS = 5
#OUTQUADS = 1

# Valid 6 x ACQ436
#OUTPAIRS = 6
#OUTQUADS = 0

DMASAMPLE = 16
DMAFILL = (DMASAMPLE - OUTPAIRS*2 - OUTQUADS*4)

MINBUFS = 4             # AWG minimum number of buffers to operate

TRASH_MARK = -32000
ENDBUF_MARK = 32700

def load_wf(args):
    data = np.fromfile(args.datafile, dtype=np.int16)
    return data


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    n = int(n)
    for i in range(0, len(l), n):
        yield l[i:i + n]


def extend_to_16_ch(args, data):
    # Assuming only 4 channels
    data_size = len(data) * 2
    data2 = [[],[],[],[]]
    data_chunks = chunks(data, len(data)/MINBUFS) # split list into 4 chunks

    for num, chunk in enumerate(data_chunks):
        # data2 = data[0:len(data)/8]
        # for index, element in enumerate(data[0::4]):
        for index in range(0,len(chunk),INCHAN):
            # duplicate AO1, AO2 for pairs and quad if exists
            for ch in range(0, OUTPAIRS+OUTQUADS):
                data2[num].append(chunk[index])
                data2[num].append(chunk[index+1])
            # then include AO3, AO4 and 4 TRASH values
            if OUTQUADS:
                data2[num].append(chunk[index+2])
                data2[num].append(chunk[index+3])
            for ch in range(0, DMAFILL):
                data2[num].append(TRASH_MARK)

    return data2


def extend_to_n_bytes(args, data):
    final_data = []
    for index, buf in enumerate(data):
        data_size = len(buf) * 2 # Data size in bytes
        pad_samples = int((args.size - data_size) / 2)
        chunk = np.append(buf, pad_samples * [ENDBUF_MARK]) # data is 1MB
        final_data.append(chunk)
        print("{} len:{} samples needed: {} data shape {}".
                format(index, len(buf), pad_samples, np.shape(final_data)))
    final_data = np.array(final_data).astype(np.int16)
    return final_data


def export_data(args, data):
    np.ndarray.tofile(data, args.out)
    return None


def make_buff(args):
    data = load_wf(args)
    data = extend_to_16_ch(args, data)
    data = extend_to_n_bytes(args, data)
    export_data(args, data)
    return None


def run_main():
    parser = argparse.ArgumentParser(description = 'AWG convert MA1 to MA2')
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
