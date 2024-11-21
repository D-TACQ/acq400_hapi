#!/usr/bin/env python3

import numpy as np
import epics
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('uut')
parser.add_argument('chan', nargs='+')
args = parser.parse_args()

nelm = int(epics.caget(f'{args.uut}:0:STREAM_SUBSET_MASK.NELM'))
print(f'nelm:{nelm}')

subset_mask = [ 0 for i in range(1,nelm+1) ]
for ic in [ int(x) for x in args.chan]: 
    subset_mask[ic] = 1

epics.caput(f'{args.uut}:0:STREAM_SUBSET_MASK', subset_mask)


