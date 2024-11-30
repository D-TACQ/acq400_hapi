#!/usr/bin/env python3
# set channels in stream subset mask for {uut} {channel ...}

import numpy as np
import epics
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('uut')
parser.add_argument('chan', nargs='+')
args = parser.parse_args()

channels = [ int(x) for x in args.chan ]

mask = 0
for ch in channels: 
    mask |= 1<<(ch-1)

subset_mask = f'0x{mask:x}'
print(f'{subset_mask}')

epics.caput(f'{args.uut}:0:STREAM_SUBSET_MASK', subset_mask)


