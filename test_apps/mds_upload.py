"""
mds_upload.py is a utility for uploading bulk raw data to an MDSplus server.

Some tips for usage:

Need to define <UUT name>_path=<server where data is stored>:://<path to UUT tree>
e.g. seg_tree_path=andros::///home/dt100/TREES/seg_tree

You must also pass the directory containing data to --data_dir at the
command line.
e.g. python mds_upload.py --data_dir=/data/<UUT name> <UUT name>
This mirrors the intended use of acq400_stream2.py (streaming to
/data/<UUT_name>).

This will upload segments of size 1kb to the specified node in the tree.
"""

import pykst
import numpy as np
import argparse
from MDSplus import *
import time
import os


def upload_segment(segment, node, startID, endID):
    start_time = Float64(startID)
    end_time = Float64(endID)
    delta = 1 / float((len(segment)))
    segment = Float32Array(segment)
    segDimension = Range(start_time, end_time, delta)
    print("seg params: ", start_time, end_time, segDimension, segment)
    node.makeSegment(start_time, end_time, segDimension, segment)


def upload_data(args):
    # upload data to the MDSplus tree.
    startID = 0
    endID = 1
    data = []
    tree = Tree(args.uuts[0], Tree.getCurrent(args.uuts[0]))
    node = tree.getNode(args.node)

    if args.store_seg == 1:
        directories = [name for name in os.listdir(args.data_dir) \
        if os.path.isdir(os.path.join(args.data_dir, name))]

        for dir in directories:
            for file in os.listdir(args.data_dir + dir):

                data.extend(np.fromfile(args.data_dir + dir + "/" + file, dtype=np.int16))

                if len(data) == args.seg_size * 1024:
                    # buffer is exact: upload data and reset buffer.
                    upload_segment(data, node, startID, endID)
                    data = []

                elif len(data) > args.seg_size * 1024:
                    # buffer too large: upload seg size and carry over rest of buffer.
                    extra_data = data[args.seg_size + 1:-1]
                    data = data[0:args.seg_size]
                    upload_segment(data, node, startID, endID)
                    data = extra_data

                elif len(data) < args.seg_size * 1024:
                    # not enough data in buffer: continue collecting data
                    continue

                startID +=1
                endID +=1

        if len(data) != 0:
            # if at any point the buffer is too big then some data will be
            # left over - this ensures any remaining data is uploaded to MDSplus.
            upload_segment(data, node, startID, endID)

    elif args.oneshot == 1:
        # upload oneshot test
        data = np.fromfile(args.data_dir + "ROOT/0000")
        node.putData(Float64Array(data))


def run_upload(args):
    if args.create_data == 1:
        create_data()
        # data = get_data()
    upload_data(args)


def run_main():
    parser = argparse.ArgumentParser(description='acq400 MDSplus interface')
    parser.add_argument('--node', default="AI", type=str, help="Which node to pull data from")
    parser.add_argument('--create_data', default="0", type=str,
                        help="Whether to create fake data and upload it to tree.")
    parser.add_argument('--samples', default="100000", type=int, help="Number of samples to read.")
    parser.add_argument('--chan', default="1", type=str, help="How many channels to push data to.")
    parser.add_argument('--store_seg', default=1, type=int, help="Whether to upload data as a segment or not.")
    parser.add_argument('--seg_size', default=1024, type=int, help="Segment size to upload to MDSplus.")
    parser.add_argument('--data_dir', default='/data/')
    parser.add_argument('--oneshot', default=1, type=int,
                        help='Whether to upload a single file, regardless of file size.')
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the data is being pulled.')
    parser.add_argument('uuts', nargs='+', help="uuts")
    run_upload(parser.parse_args())


if __name__ == '__main__':
    run_main()