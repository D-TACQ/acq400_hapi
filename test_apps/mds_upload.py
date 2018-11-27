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


import numpy as np
import argparse
from MDSplus import *
import os


def upload_segment(segment, node, segID):
    start_time = Float64(segID)
    end_time = Float64(segID+1)
    delta = 1 / float((len(segment)))
    segment = Float32Array(segment)
    segDimension = Range(start_time, end_time, delta)
    # print("seg params: ", start_time, end_time, segDimension, segment)
    node.makeSegment(start_time, end_time, segDimension, segment)


def upload_data(args):
    # upload data to the MDSplus tree.
    segID = 0
    data = []
    tree = Tree(args.uuts[0], Tree.getCurrent(args.uuts[0]))
    node = tree.getNode(args.node)

    if args.store_seg == 1:
        directories = [name for name in os.listdir(args.data_dir) if os.path.isdir(os.path.join(args.data_dir, name))]
        for dir1 in directories:
            print dir1
            for file in os.listdir(args.data_dir + dir1):

                data.extend(np.fromfile(args.data_dir + dir1 + "/" + file, dtype=np.int16))
                upload_segment(data, node, segID)
                data = []
                segID += 1
                print
                "file uploaded"

def run_upload(args):

    upload_data(args)


def run_main():
    parser = argparse.ArgumentParser(description='acq400 MDSplus interface')
    # parser.add_argument('-filesize', '--filesize', default=0x100000, action=acq400_hapi.intSIAction, decimal=False)
    parser.add_argument('--node', default="AI", type=str, help="Which node to pull data from")
    parser.add_argument('--store_seg', default=1, type=int, help="Whether to upload data as a segment or not.")
    parser.add_argument('--data_dir', default='/data/')
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the data is being pulled.')
    parser.add_argument('uuts', nargs='+', help="uuts")
    run_upload(parser.parse_args())


if __name__ == '__main__':
    run_main()