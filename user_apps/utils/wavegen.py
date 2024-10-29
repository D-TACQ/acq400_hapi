#!/usr/bin/env python3

"""
Usage:

# 16 chans 32 bit +11.5 degrees phase offset per channel
./wavegen.py --nchan=16 --dsize=4 --phase=+11.5

# 8 chans 32 bit even channels half scale
./wavegen.py --nchan=8 --dsize=4 --scale=0.5:EVEN

# 3 chans different wave functions on each
./wavegen.py --nchan=3 --wave=SINE:1/RAMP:2/SQUARE:3


"""

import argparse
import numpy as np
import time
from matplotlib import pyplot as plt

class WaveGen():

    def __init__(
            self, 
            nchan, 
            cycles, 
            wavelength,
            totallength,
            dsize, 
            wave, 
            phase, 
            scale,  
            crop, 
            spos, 
            **kwargs
        ):
        self.nchan = nchan
        self.cycles = cycles
        self.phase = phase
        self.crop = crop
        self.spos = spos

        self.wavelength = self.__init_wavelength(wavelength)
        self.totallength = totallength if totallength else self.wavelength
        self.datalength = self.totallength * nchan

        #print(f"wavelength {self.wavelength} totallength {self.totallength} datalength {self.datalength}")

        self.dtype = self.__init_dtype(dsize)
        self.scale = self.__init_scale(scale)
        self.wave = self.__init_wave(wave)

        self.filename = f"{self.nchan}CH.{self.dlen}B.{self.totallength}.{self.cycles}CYCL.{int(time.time())}"

        self.last = {}

    def __init_wavelength(self, wavelength):
        self.wavelengths = wavelength
        return int(wavelength[0]) * self.cycles

    def __init_scale(self, scale):
        scale_map = {}
        for value in scale.split('/'):
            selector, channels = value.split(':')
            scale_map.update({chan: selector for chan in self.get_channels(channels)})
        return scale_map
    
    def __init_wave(self, wave):
        wave_funcs = {
            'SINE': self.__gen_sine,
            'RAMP': self.__gen_ramp,
            'SQUARE': self.__gen_square,
        }
        wave_map = {}
        for value in wave.split('/'):
            selector, channels = value.split(':')
            wave_map.update({chan: wave_funcs[selector] for chan in self.get_channels(channels)})
        return wave_map

    def get_channels(self, chans):
        if chans.upper() == 'ALL': return list(range(1, self.nchan + 1))
        if chans.upper() == 'ODD': return list(range(1, self.nchan + 1, 2))
        if chans.upper() == 'EVEN': return list(range(2, self.nchan + 1, 2))
        channels = []
        for chan in chans.split(','):
            if '-' in chan:
                chan = list(map(int, chan.split('-')))
                channels.extend(list(range(chan[0], chan[1] + 1)))
                continue
            channels.append(int(chan))
        return channels

    def __init_dtype(self, dsize):
        if dsize in [2, 16]:
            dtype = np.int16
            self.dlen = 2
        elif dsize in [4, 32]:
            dtype = np.int32
            self.dlen = 4
        else:
            raise ValueError(f"dsize is invalid '{dsize}'")
        self.max_value = np.iinfo(dtype).max
        return dtype
        
    def generate(self):
        print(f"Generating {self.nchan} Chans @ {self.dlen}Bytes * {self.totallength} Samples")
        self.data = np.zeros(self.datalength, dtype=self.dtype)
        self.view = self.data.reshape(-1, self.nchan).T
        for chan in range(self.nchan):
            gen_wave = self.__get_wave(chan + 1)
            if not gen_wave: continue
            scale = self.__get_scale(chan + 1)

            wavelength = self.__get_wavelength(chan)
            phase = self.__get_phase(chan)
            crop = self.__get_crop(chan)
            spos = self.__get_spos(chan)

            d0 = min(0 + spos, self.totallength)
            d1 = min(d0 + wavelength - crop, self.totallength)

            w0 = 0
            w1 = d1 - d0 
         
            print(f"CH {chan + 1} {gen_wave.__name__} phase[{phase}] spos[{spos}] scale[{scale}] wavelength[{wavelength}] crop[{crop}]")
            #print(f"[{d0}:{d1}] <- [{w0}:{w1}]")
            self.data[chan::self.nchan][d0:d1] = (gen_wave(wavelength, phase) * (self.max_value * scale)).astype(self.dtype)[w0:w1]

    def __get_wave(self, chan):
        if chan in self.wave:
            return self.wave[chan]
        return None
    
    def __get_scale(self, chan):
        if chan in self.scale:
            return float(self.scale[chan])
        return 1
    
    def __cycler_generic(self, chan, arr, last_key, zerostart=False):
        if last_key not in self.last:
            self.last[last_key] = 0
        value = arr[chan % len(arr)]
        preval = 0
        signed = False
        if str(value).startswith(('+', '-')):
            signed = True
            preval = self.last[last_key]
        value = float(value)
        #print(f"{last_key} CH {chan +1}, arr{arr} value {value} {preval} last {self.last[last_key]} ")       
        self.last[last_key] = value + preval
        if zerostart and signed: return preval
        return self.last[last_key]
    
    def __get_crop(self, chan):
        return int(self.__cycler_generic(chan, self.crop, "precrop"))
    
    def __get_wavelength(self, chan):
        return int(self.__cycler_generic(chan, self.wavelengths, "prewave")) * self.cycles

    def __get_phase(self, chan):
        return np.deg2rad(self.__cycler_generic(chan, self.phase, "prephase", zerostart=True))
    
    def __get_spos(self, chan):
        return int(self.__cycler_generic(chan, self.spos, "prespos", zerostart=True))
    
    def __gen_sine(self, wavelength, phase):
        return np.sin(np.linspace(-phase, -phase + (self.cycles * 2) * np.pi, wavelength))
    
    def __gen_ramp(self, wavelength, phase):
        return np.mod(np.linspace(0, self.cycles, wavelength) + phase, 1)
    
    def __gen_square(self, wavelength, phase):
        return np.sign(self.__gen_sine(wavelength, phase))
    
    def plot(self):
        print(f'Plotting')
        for chan in range(self.nchan):
            plt.plot(self.data[chan::self.nchan], label=f"CH{chan + 1}")
        plt.title(self.filename)
        plt.xlabel("Samples")
        plt.ylabel("Codes")
        plt.legend()
        plt.show()

    def save(self):
        filename = f"{self.filename}.dat"
        self.data.tofile(f"{self.filename}.dat")
        print(f"wave data saved to {filename}")


def run_main(args):
    wave = WaveGen(**vars(args))
    wave.generate()

    if args.plot:
        wave.plot()

    if args.save:
        wave.save()

def comma_list(arg):
    return arg.split(',')

def get_parser():    
    parser = argparse.ArgumentParser(description="Waveform generator helper")

    parser.add_argument('--nchan', default=8, type=int, help="total channels")
    parser.add_argument('--cycles', default=1, type=int, help="cycles in waveform")
    parser.add_argument('--wavelength', default=[20000], type=comma_list, help="wavelength in samples")
    parser.add_argument('--totallength', default=None, type=int, help="total channel length override")
    parser.add_argument('--dsize', default=2, type=int, help="data size 2,16 or 4,32")

    parser.add_argument('--wave', default="SINE:ALL", help="wave func and targeted channels (SINE:1,2,3,4/RAMP:5,6,7,8)")
    parser.add_argument('--scale', default="1:ALL", help="scale and targeted channels (1:EVEN/0.5:ODD)")

    parser.add_argument('--phase', default=[0], type=comma_list, help="phase value in degrees (45 or +45 or 45,90,135, 180)")

    parser.add_argument('--spos', default=[0], type=comma_list, help="start position to insert waveform")
    parser.add_argument('--crop', default=[0], type=comma_list,  help="crop waveform by x samples") 

    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--save', default=0, type=int, help="Save data")

    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())

