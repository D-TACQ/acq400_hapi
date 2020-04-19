#!/usr/bin/env python
"""

scans mr data for MR transitions.
default: works on the ACQ2106, reading /dev/acq400/data/1/01

"""

import numpy as np
import argparse


def mr_count(args):
	ch01 = np.fromfile(args.chfile, dtype=np.int16)

	print("{} len {}".format(args.chfile, len(ch01)))

	mm1 = 3

	for ix, raw in enumerate(ch01):
		mode = raw&3
		if mode != mm1:
			print("{:8d} : {:d}=>{:d}".format(ix, mm1, mode))
			mm1 = mode

def run_main():
    parser = argparse.ArgumentParser(description='acq2106_mr_count')
    parser.add_argument('--chfile', default="/dev/acq400/data/1/01", help="uuts")
    mr_count(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
