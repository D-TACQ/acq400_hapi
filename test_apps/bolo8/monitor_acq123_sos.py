#!/usr/bin/env python3
import gzip
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import sys

import get_calibfit
########################################################################
# Read and reshape the data.
########################################################################
#SOURCE = './DATA/acq2106_123_CH00'
SOURCE = f'./DATA/{sys.argv[1]}_CH00'
NBOLO = 2
NPHYSICAL = NBOLO * 8
NLOGICAL = NPHYSICAL * 3
FS = 1e4  # Sample rate is 10 kSPS

# Multiplexed data
raw = np.fromfile(SOURCE, dtype='int32')  # If source in uncompressed
#with gzip.open(SOURCE, 'rb') as f:  # For compressed source
#    raw = np.frombuffer(f.read(), dtype='int32')
# Demuxed into logical channels
raw2d = raw.reshape((NLOGICAL, -1), order='F')
# Demuxed and unpacked into physical quantities
mag, phase, pwr = raw2d.reshape((NPHYSICAL, 3, -1)).transpose(1, 0, 2)

# Convert to physical units
A = mag * 1.25 * 5.688e-8  # Assume 1V25 gain setting
phi = phase * 1.863e-9
P = pwr * 1.25 * 3.64e-6

time_vector = np.arange(mag.shape[-1]) / FS

active1 = (9, 10, 11)
active = [ i-1 for i in active1 ]

if A[active[0], 20:].max() < A[active[1], 20:].max():
    print(f" ERROR detected ch:{active[0]} max:{A[active[0], 20:].max()} < ch:{active[1]} max:{A[active[1], 20:].max()}")
    sys.exit(1)
if A[active[0], 20:].max() < A[active[2], 20:].max():
    print(f" ERROR detected ch:{active[0]} max:{A[active[0], 20:].max()} < ch:{active[2]} max:{A[active[2], 20:].max()}")
    sys.exit(1)

print("Max limits OK, continue")
sys.exit(0)



