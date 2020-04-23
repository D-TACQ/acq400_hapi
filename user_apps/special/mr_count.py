#!/usr/bin/env python
"""

scans mr data for MR transitions.
default: works on the ACQ2106, reading /dev/acq400/data/1/01

"""

import numpy as np
import argparse

def crossings_nonzero_pos2neg(data):
    pos = data > 0
    return len((pos[:-1] & ~pos[1:]).nonzero()[0])

def mr_count(args):
	ch01 = np.fromfile(args.chfile, dtype=np.int16)

	print("{} len {}".format(args.chfile, len(ch01)))

	mm1 = 3
	i0 = 0

	for ix, raw in enumerate(ch01):
		mode = raw&3
		if mode != mm1:
			if ix > 0:
				edges = crossings_nonzero_pos2neg(ch01[i0:ix-1])
				print("{:8d} : {:d}=>{:d} crossings {}".format(ix, mm1, mode, edges))
			mm1 = mode
			i0 = ix

def run_main():
    parser = argparse.ArgumentParser(description='acq2106_mr_count')
    parser.add_argument('--chfile', default="/dev/acq400/data/1/01", help="uuts")
    mr_count(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
