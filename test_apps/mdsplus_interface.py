"""
mdsplus_interface.py is a python interface to MDSplus. It is designed to be used similarly to dwscope, but supposed to
use KST2 to plot data.

"""

import pykst
import numpy as np
import argparse
import acq400_hapi
from MDSplus import *


def plot_data(args, data):
    client = pykst.Client("NumpyVector")
    V2 = client.new_editable_vector(data.astype(np.float64))
    ydata = np.array(list(range(0, len(data)))).astype(np.float64)
    V1 = client.new_editable_vector(ydata)
    c1 = client.new_curve(V1, V2)
    p1 = client.new_plot()
    # p1.set_left_label(yu)
    # p1.set_bottom_label(xu)
    # print(p1)
    p1.add(c1)


def get_data(args):

    shot = Tree(args.uuts[0], args.shot)
    try:
        node = shot.getNode(args.node + str(args.chan))
    except:
        print("Node not found. Make sure node exists. Node = ", args.node + str(args.chan))
        raise SystemExit
    # chan = args.chan
    data = node.getData().data()
    return data


def run_plot(args):
    data = get_data(args)
    plot_data(args, data)


def run_main():
    parser = argparse.ArgumentParser(description='acq400 MDSplus interface')
    # parser.add_argument('--tree', default=1024, type=int, help=".")
    parser.add_argument('--node', default="AI", type=str, help="Which node to pull data from")
    parser.add_argument('--samples', default="100000", type=int, help="Number of samples to read.")
    parser.add_argument('--shot', default=-1, type=int, help="Which shot to pull data from.")
    parser.add_argument('--chan', default=01, type=int, help="How many channels to pull data from.")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the data is being pulled.')
    parser.add_argument('uuts', nargs='+', help="uuts")
    run_plot(parser.parse_args())


if __name__ == '__main__':
    run_main()
