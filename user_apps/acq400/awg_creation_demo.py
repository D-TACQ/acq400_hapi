#!/usr/bin/env python


"""
This script will generate a binary file that can be used to output a waveform on D-TACQ AO modules.

To have the UUT output a single sample the file should have 32 int16s ie (CH1 CH2 ... CH32) where the value for each
channel can be different (they will not be different for this example). The user can extend this to as many samples as
necessary and to any value necessary i.e the values do not need to be the same across channels (channel 1 could be a
sine wave, channel 2 could be a sinc wave etc).

In this script we are outputting the same identical sine wave across all 32 channels for nsam number of samples.
There is also an argument called even_ch_to_zeros that, if set, will set all of the even channels to zero to illustrate
how the channels are ordered.

Example usage:

To create the default file:

python awg_creation_demo.py

To create binary file with even channels set to 0 and a wave size of 3000 samples.

python awg_creation_demo.py --nsam=3000 --even_ch_to_zeros=1



To upload awg files once it has been generated use the following python script:

python acq1001_awg_demo.py --files="../acq400/waves/example_awg" --capture=1 --awglen=<awg_length> <UUT name>
"""


import numpy as np
import matplotlib.pyplot as plt
import re
import argparse


def create_array(nsam, args):

    # function that creates an array with nsam * nchan elements

    # Firstly, an array containing a sine wave is generated. This is entirely arbitrary and is meant to demonstrate a
    # waveform being generated. We scale the sine wave by 32767 because the DACs are 16 bit.
    # DAC codes valid in range -32768 to 32767. If the UUT gets a code of 32768 the output will just saturate. Also
    # be aware that the astype(np.int16) function used below will wrap back to -32768 if a number larger than 32767 is
    # used. The same goes for numbers < -32768: they wrap up to 32767.

    limit = 2*np.pi*args.w 
    fxn = args.fx(np.linspace(-limit/2, limit/2, nsam)) # Creates sine wave
    fxn = 32767 * fxn # Scales the sine wave to 16 bit
    fxn = np.rint(fxn) # round the sine wave to integers

    # An empty list is created that will eventually contain our waveform
    waveform = []

    # For every point in the sine wave: duplicate it nchan times (one value for each one of the channels)
    for num in fxn:
        waveform.extend(args.nchan*[num]) # extends the single value taken from the sine wave data across 32 channels.

    if args.even_ch_to_zeros == 1: # if this argument is chosen then all of the even channels will be set to 0.

        for index, element in enumerate(waveform): # loop over all of the channels in order

            if index % 2 != 0: # if the index of that channel is odd then set it to 0.
                               # We check for odd channels here because in python we index from 0, whereas real
                               # channels are indexed from 1.

                waveform[index] = 0 # Here we set the value of the "even" channel to 0.

    # change waveform into a numpy array so we can use numpy functions on it.
    waveform = np.array(waveform)

    # We then ensure that the waveforms points are of type int16. This is important as the UUT requires the data type
    # to be int16.
    waveform = waveform.astype(np.int16)
    return waveform


def generate_awg(args):
    waveform = create_array(args.nsam, args)
    fname = args.fn.split(".")
    if len(fname) == 1:
        fname = fname[0]
    else:
        fname = fname[1]

    waveform.tofile("{}/{}-{}-{}.dat".format(args.dir, "{}{}".format(fname, "" if args.w == 1 else str(args.w)), args.nchan, args.nsam), "")


def run_main():
    parser = argparse.ArgumentParser(description='generate awg waveform')
    parser.add_argument('--fn', default='np.sin', help="Generator function default:np.sin()")
    parser.add_argument('--w', default=1, type=int, help="Angular frequency")
    parser.add_argument('--nsam', default=30000, type=int, help="Size of wave to generate.")
    parser.add_argument('--nchan', default=32, type=int, help="Number of channels in AO module.")
    parser.add_argument('--even_ch_to_zeros', default=0, type=int, help="Whether to set even channels to zero.")
    parser.add_argument('--dir', default="waves", type=str, help="Location to save files")
    parser.
    args = parser.parse_args()
    args.fx = eval(args.fn)
    generate_awg(args)


if __name__ == '__main__':
    run_main()
