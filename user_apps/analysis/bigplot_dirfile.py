#!/usr/bin/python
"""
bigplot_dirfile.py

acq400_upload and other tools generate "DirFiles",
a directory with file-per-channel.

kst2 plot can have direct support for DirFile, but more often than not,
it's missing.

pykst lets us do the same thing..

"""

import pykst
import numpy as np
import argparse
import os
import re

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
     
def process_data(args):
    args.chd = { k:1 for k in list_decode(args.ch) }

    dir = args.dirfile[0]
    ch_files = get_ch_files(dir)
        
    chx = [ np.fromfile("{}/{}".format(dir, f), dtype='int16') \
			for f in ch_files if ch_selected(f, args.chd) ]
    llen = len(chx[0])
    print("plotting {} {}M points".format(llen, llen/1e6))
    xsam = np.linspace(0, llen, num=llen)
    client = pykst.Client(dir)
    XX = client.new_editable_vector(xsam, name="samples")
    ix = 0
    for f in ch_files:
        if ch_selected(f, args.chd):
            YY = client.new_editable_vector(chx[ix].astype(np.float64), name=title(f))
            client.new_plot().add(client.new_curve(XX, YY))
            ix = ix + 1

def run_main():
    parser = argparse.ArgumentParser(description='plot a dirfile')
    parser.add_argument('--ch', default=':', help='channel list, default : all')
    parser.add_argument('dirfile', nargs=1, help='directory with dirfile')
    process_data(parser.parse_args())

if __name__ == '__main__':
    run_main()

