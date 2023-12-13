#!/usr/bin/python
"""
bigplot_dirfile.py

acq400_upload and other tools generate "DirFiles",
a directory with file-per-channel.

kst2 plot can have direct support for DirFile, but more often than not,
it's missing.

pykst lets us do the same thing..

"""

import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
import re

has_pykst = False
if os.name != "nt":
    try:
        import pykst
        has_pykst = True
    except ImportError:
        print("WARNING: failed to import pykst, no kst plots")
def get_ch_files(dir):
    ch_files = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if '_CH' in file:
                ch_files.append(file)

    return ch_files

def title(t1):
    return re.sub(r"_", r"\_", t1)

# remove me .. make ui lib fun
def list_decode(list_def):
    if (list_def == ':'):
        return range(1, 100)
    else:
        r2 = list_def.split(':')
        if len(r2) == 2:
            return range(int(r2[0]), int(r2[1])+1)
        else:
            return eval('( {} , )'.format(list_def))


def ch_selected(chfile, chd):
    p = re.compile(r'.*_CH([0-9]{2})')
    m = p.search(chfile)
    if m == None:
        return False
    try:
        sel = chd[int(m.group(1))]
        return True
    except KeyError:
        return False

def plot_kst(args, chx):         
    llen = len(chx[0])
    print("plotting {} {}M points".format(llen, llen/1e6))
    xsam = np.linspace(0, llen, num=llen)    
    client = pykst.Client(args.dirfile[0])
    XX = client.new_editable_vector(xsam, name="samples")
    ix = 0
    for f in get_ch_files(args.dirfile[0]):
        if ch_selected(f, args.chd):
            YY = client.new_editable_vector(chx[ix].astype(np.float64), name=title(f))
            print("adding plot {}".format(f))
            client.new_plot().add(client.new_curve(XX, YY))
            ix = ix + 1 

def plot_matplot(args, chx):
    nch = len(chx)
    f, plots = plt.subplots(nch, 1)
    for num, sp in enumerate([f for f in get_ch_files(args.dirfile[0]) if ch_selected(f, args.chd) ]):
        plots[num].plot(chx[num])
    plt.show()
    

def process_data(args):    
    args.chd = { k:1 for k in list_decode(args.ch) }
#    print(args.chd)      
#   print("ch_files: {}".format(get_ch_files(args.dirfile[0])))
    
    chx = [ np.fromfile("{}/{}".format(args.dirfile[0], f), dtype='int16') \
            for f in get_ch_files(args.dirfile[0]) if ch_selected(f, args.chd) ]
    
    if has_pykst == False or args.matplot == 1:
        plot_matplot(args, chx)
    else:
        plot_kst(args, chx)



def get_parser():
    parser = argparse.ArgumentParser(description='plot a dirfile')
    parser.add_argument('--matplot', type=int, default=0, help='use matplot to plot, not kst')
    parser.add_argument('--ch', default=':', help='channel list, default : all')
    parser.add_argument('dirfile', nargs=1, help='directory with dirfile')
    return parser

if __name__ == '__main__':
    process_data(get_parser().parse_args())

