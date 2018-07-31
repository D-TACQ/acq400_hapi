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

def process_data(args):
    dir = args.dirfile[0]
    ch_files = get_ch_files(dir)
    chx = [ np.fromfile("{}/{}".format(dir, f), dtype='int16') \
			for f in ch_files ]
    llen = len(chx[0])
    xsam = np.linspace(0, llen, num=llen)
    client = pykst.Client(dir)
    XX = client.new_editable_vector(xsam, name="samples")
    ix = 0
    for f in ch_files:
        YY = client.new_editable_vector(chx[ix].astype(np.float64), name=title(f))
        client.new_plot().add(client.new_curve(XX, YY))
        ix = ix + 1

def run_main():
    parser = argparse.ArgumentParser(description='plot a dirfile')
    parser.add_argument('dirfile', nargs=1, help='directory with dirfile')
    process_data(parser.parse_args())

if __name__ == '__main__':
    run_main()

