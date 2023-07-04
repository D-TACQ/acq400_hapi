#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

########################################################################
# Read and reshape the data.
########################################################################
SOURCE = './DATA/acq2106_123_CH00'
NBOLO = 2
NPHYSICAL = NBOLO * 8
NLOGICAL = NPHYSICAL * 3
FS = 1e4  # Sample rate is 10 kSPS

# Multiplexed data
raw = np.fromfile(SOURCE, dtype='int32')
# Demuxed into logical channels
raw2d = raw.reshape((NLOGICAL, -1), order='F')
# Demuxed and unpacked into physical quantities
mag, phase, pwr = raw2d.reshape((NPHYSICAL, 3, -1)).transpose(1, 0, 2)

# Convert to physical units
A = mag * 1.25 * 5.688e-8  # Assume 1V25 gain setting
phi = phase * 1.863e-9
P = pwr * 1.25 * 3.64e-6

time_vector = np.arange(mag.shape[-1]) / FS

########################################################################
# Plot the magnitude to verify we've read the correct data.
########################################################################
plt.figure()
plt.plot(time_vector[20:], A[[9-1, 10-1, 11-1], 20:].T)
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

sens = np.full(NPHYSICAL, np.nan)
sens[[9-1, 10-1, 11-1]] = [3.74, 4.24, 4.19]    # copy from today's cal
tau = np.full(NPHYSICAL, np.nan)
tau[[9-1, 10-1, 11-1]] = [0.046, 0.046, 0.046]

# Give sens and tau the right broadcasting behaviour.
sens = sens[:, None]
tau = tau[:, None]

Pcalc = 1/sens * (A + tau * dAdt)

# First 20 samples are contaminated by the filter warm up.
Pcalc[:, :20] = np.nan

plt.figure()
plt.plot(time_vector, Pcalc[[9-1, 10-1, 11-1]].T)
plt.ylabel('Absorbed power [W]')
plt.xlabel('Time [s]')

########################################################################
# Fix the offset correction.
########################################################################

# Offset correction is not quite right, particularly for channel 10, which
# is why we don't get a perfect square wave. If offset correction was perfect
# the phase would be constant, but it varies slightly with the magnitude.
plt.figure()
plt.plot(time_vector[20:], phi[[9-1, 10-1, 11-1], 20:].T)
plt.ylabel('Phase [radians]')
plt.xlabel('Time [s]')

# Try improving the offset correction in post-processing. Here I'm doing it
# by trial and error, but in a tokamak environment one would record some data
# before the start of the plasma and use that to re-baseline.
# I'm planning to add a '/usr/local/bin/remove_bolo_offset' script to do
# this automatically when I get the time.
V = A * np.exp(-1j * phi)
I0 = np.zeros(NPHYSICAL)
Q0 = np.zeros(NPHYSICAL)
I0[[9-1, 10-1, 11-1]] = [-7e-4, 4.3e-3, 4.3e-3]
Q0[[9-1, 10-1, 11-1]] = [2e-4, -5.5e-3, -5.5e-3]

offsets = I0 - 1j * Q0
offsets = offsets[:, None]
Vcorr = V - offsets

# If the offset correction is accurate, the phase should be more constant.
# At least, it shouldn't vary significantly with the amplitude.
plt.figure()
plt.plot(time_vector[20:], np.angle(Vcorr)[[9-1, 10-1, 11-1], 20:].T)
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
Pccorr[:, :20] = np.nan + 1j * np.nan
Pcorr = abs(Pccorr)

plt.figure()
plt.plot(time_vector, Pcorr[[9-1, 10-1, 11-1]].T)
plt.ylabel('Absorbed power, offset corrected [W]')
plt.xlabel('Time [s]')

plt.show()
