#!/usr/bin/env python3
import gzip
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

import get_calibfit
import sys
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
calib = get_calibfit.Calibfit('acq2106_123')

########################################################################
# Plot the magnitude to verify we've read the correct data.
########################################################################
plt.figure()
plt.plot(time_vector[20:], A[active, 20:].T)
plt.ylabel('Magnitude [V]')
plt.xlabel('Time [s]')

########################################################################
# Calculate the incident power using the bolometer equation.
########################################################################
# Smooth the derivative a bit.
dA = signal.savgol_filter(A, window_length=20, polyorder=3, deriv=1, axis=-1)
dt = 1 / FS
dAdt = dA / dt
# Could also do dAdt = np.gradient(A, FS, axis=-1) if not concerned with noise.

# Assume the calibration constants are the same as the last data set I got.
sens = np.full(NPHYSICAL, np.nan)
sens[active] = [ calib.sns(ic) for ic in active1]
#sens[active] = [3.72, 4.22]
tau = np.full(NPHYSICAL, np.nan)
tau[active] = [ calib.tau(ic) for ic in active1]
#tau[[9-1, 10-1]] = [0.046, 0.046]
# We actually get a slightly better square wave by increasing the cooling
# time a bit. Consider re-running with a fresh calibration.
#tau[[9-1, 10-1]] = [0.053, 0.054]

# Give sens and tau the right broadcasting behaviour.
sens = sens[:, None]
tau = tau[:, None]

Pcalc = 1/sens * (A + tau * dAdt)

# First 20 samples are contaminated by the filter warm up.
Pcalc[:, :20] = np.nan

plt.figure()
plt.plot(time_vector, Pcalc[active].T)
plt.ylabel('Absorbed power [W]')
plt.xlabel('Time [s]')

########################################################################
# Fix the offset correction.
########################################################################

# Offset correction is not quite right, particularly for channel 10, which
# is why we don't get a perfect square wave. If offset correction was perfect
# the phase would be constant, but it varies slightly with the magnitude.
plt.figure()
plt.plot(time_vector[20:], phi[active, 20:].T)
plt.ylabel('Phase [radians]')
plt.xlabel('Time [s]')

# Try improving the offset correction in post-processing. We have a period
# at the start of the capture with zero power: use this to work out the
# offset as accurately as possible.
V = A * np.exp(-1j * phi)
# Offset for al channels is taken as the average value in the first 1000
# samples, ignoring a few early samples to ensure there is no filter
# warmup left over.
offsets = V[:, 100:1000].mean(axis=-1)

offsets = offsets[:, None]
Vcorr = V - offsets

# If the offset correction is accurate, the phase should be more constant.
# At least, it shouldn't vary significantly with the amplitude.
plt.figure()
plt.plot(time_vector[20:], np.angle(Vcorr)[active, 20:].T)
plt.ylabel('Phase with offset correction [radians]')
plt.xlabel('Time [s]')

########################################################################
# Recalculate the power with the offset correction done more accurately.
########################################################################

# Match how BOLODSP calculates the real time PWR signal: smooth and differentiate
# the real and complex parts of the voltage seprately, then take the magnitude at
# the end.
Pccorr = np.zeros_like(Vcorr)
Pccorr.real = (1/sens) * (Vcorr.real + tau * signal.savgol_filter(Vcorr.real, 20, 3, 1, axis=-1) / dt)
Pccorr.imag = (1/sens) * (Vcorr.imag + tau * signal.savgol_filter(Vcorr.imag, 20, 3, 1, axis=-1) / dt)
# Invalidate samples contaiminated by FPGA filter warmup and the Sav-Gol filter.
Pccorr[:, :25] = np.nan + 1j * np.nan
Pcorr = abs(Pccorr)

plt.figure()
plt.plot(time_vector, Pcorr[active].T)
plt.ylabel('Absorbed power, offset corrected [W]')
plt.xlabel('Time [s]')

plt.show()
