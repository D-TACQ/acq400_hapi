#!/usr/bin/python

# simplest possible load data and plot example
# Set DATAFILE to some valid muxed binary file, check the stride, run

import numpy as np
import matplotlib.pyplot as plt

# DATAFILE is a sample mux data set N x 16 channels, 16 bit
DATAFILE="/data/acq1001_329/2690"
chx = np.fromfile(DATAFILE, dtype='int16')
# Plot first channel CH01, all the data. Stride 16 to pick out CH01 only
plt.plot(chx[0::16])
plt.show()
