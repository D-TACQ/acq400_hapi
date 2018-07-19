"""
mdsplus_interface.py is a python interface to MDSplus. It is designed to be used similarly to dwscope, but supposed to
use KST2 to plot data.

Usage:

    python mdsplus_interface.py --chan=1:16 --shot=69 acq2106_054

        This will read channels 1 to 16 (inclusive) of the acq2106_054 tree and reads from the default AI node.

"""

import pykst
import numpy as np
import argparse
from MDSplus import *


def plot_data(args, data):
    client = pykst.Client("NumpyVector")
    p1 = client.new_plot()
    for counter, chn in enumerate(data):
        V2 = client.new_editable_vector(chn.astype(np.float64))
        ydata = np.array(list(range(0, len(chn)))).astype(np.float64)
        V1 = client.new_editable_vector(ydata)
        c1 = client.new_curve(V1, V2)
        p1.set_top_label("Channel {}".format(counter+1))
        p1.add(c1)
        if not args.overlay and counter + 1 < len(data):
            p1 = client.new_plot()


def plot_segmented_data(args, data):
    client = pykst.Client("NumpyVector")
    p1 = client.new_plot()
    V2 = client.new_editable_vector(data.astype(np.float64))
    ydata = np.array(list(range(0, len(data)))).astype(np.float64)
    V1 = client.new_editable_vector(ydata)
    c1 = client.new_curve(V1, V2)
    p1.set_top_label("Channel {}".format("1"))
    p1.add(c1)
    # if not args.overlay and counter + 1 < len(data):
    #     p1 = client.new_plot()


def get_seg_data(args):
    tree = Tree("seg_tree", 2)
    #Tree.setTimeContext(None, None, args.rate)
    Tree.setTimeContext(None, None, 1E-6)
    node = tree.getNode("RAW_SEG.RAW")
    data = node.data()
    print("data = ", data)
    return data


def get_data(args):
    data = []
    if args.shot == -1:
        args.shot = Tree.getCurrent(args.uuts[0])
    tree = Tree(args.uuts[0], args.shot)
    args.chan = args.chan.split(":")
    channels = list(range(int(args.chan[0]), int(args.chan[-1])+1))
    for chn in channels:
        try:
            if chn < 10:
                node = tree.getNode(args.node + "." + "CH0" + str(chn))
            elif chn < 100:
                node = tree.getNode(args.node + "." + "CH" + str(chn))
        except:
            print("Node not found. Make sure node exists. Node = ", node)
            raise SystemExit
        data.append(node.getData().data())
    return np.array(data)


def run_plot(args):
    if args.seg == 0:
        data = get_data(args)
        plot_data(args, data)
    else:
        data = get_seg_data(args)
        plot_segmented_data(args, data)


def run_main():
    parser = argparse.ArgumentParser(description='acq400 MDSplus interface')
    parser.add_argument('--node', default="AI", type=str, help="Which node to pull data from")
    parser.add_argument('--samples', default="100000", type=int, help="Number of samples to read.")
    parser.add_argument('--shot', default=-1, type=int, help="Which shot to pull data from.")
    parser.add_argument('--chan', default="1", type=str, help="How many channels to pull data from.")
    parser.add_argument('--overlay', default=0, type=int, help="Whether to overlay the channel data or to give each channel its own plot.")
    parser.add_argument('--seg', default=0, type=int, help="Whether the data from in the tree is segmented or not.")
    parser.add_argument('--rate', default=1000000, type=int, help="Whether the data from in the tree is segmented or not.")
    parser.add_argument('--verbose', default=0, type=int, help='Prints status messages as the data is being pulled.')
    parser.add_argument('uuts', nargs='+', help="uuts")
    run_plot(parser.parse_args())


if __name__ == '__main__':
    run_main()

