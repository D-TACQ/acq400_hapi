#!/usr/bin/env python3
'''
paste two binary files assume single column uint32
eg to make a 2xDIO422 wave pattern
'''


import numpy as np
import sys

def run_main():
    SRC = sys.argv[1]
    DST = "{}.2x32".format(SRC)

    raw1 = np.fromfile(SRC, np.uint32)
    raw2 = np.dstack((raw1,raw1))

    print(raw1.shape,raw2.shape)

    with open(DST, 'wb') as fp:
        raw2.tofile(fp)

if __name__ == '__main__':
    run_main()

