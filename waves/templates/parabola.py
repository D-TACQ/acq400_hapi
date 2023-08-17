#!/usr/bin/env python3
'''
Created on 14 Aug 2023

@author: pgm
'''

import numpy as np

import argparse
import os

import common

'''
create a parabola
'''


'''
parabola:
>>> import matplotlib.pyplot as plt
>>> import numpy as np
>>> x  = np.linspace(-50,50,100)
>>> y = x**2
>>> plt.plot(x,y)

(python:160122): Gtk-WARNING **: 20:54:28.290: Theme parsing error: gtk.css:11:22: The :focused pseudo-class is deprecated. Use :focus instead.
[<matplotlib.lines.Line2D object at 0x7fc00ad17010>]
>>> plt.show()

'''

def parabola(nsamples, post, amplitude, offset):
    xx = np.linspace(-nsamples//2,nsamples//2,nsamples)
    yy = offset + amplitude/((nsamples/2)**2) * xx**2
    
    return np.pad(yy, (0, post),'constant', constant_values=(0, yy[-1]))

    
def ui(cmd_args=None):
    nsam = 512
    post = 0    
    amp = 16000
    offset = 0
    
    parser = argparse.ArgumentParser(description="parabola", prog="parabola",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--nsam', default=nsam, type=int, help='nsam: samples in parabola')
    parser.add_argument('--post', default=post, type=int, help='post: flat line after end')
    parser.add_argument('--amp',  default=amp, type=int, help='Amplitude negative values accepted')
    parser.add_argument('--offset',  default=offset, type=int, help='Offset negative values accepted')
    return common.ui(parser, cmd_args)

class ParabolaWrapper:
    def __call__(self, args):
        self.args = args
        return parabola(args.nsam, args.post, args.amp, args.offset)
    def __str__(self):
        args = self.args
        return f'{args.root}/parabola-x{args.reps}-{args.nsam}-{args.post}-{args.amp}-{args.offset}_{args.ch}.dat'

def parabola_from_cmd(cmd_args):
    return common.exec_command(ui(cmd_args), ParabolaWrapper())
 
# unit test: plots the data  
if __name__ == '__main__':
    data, fn = parabola_from_cmd(None)
    common.plot(data, fn)
else:
    common.WAVE_CMDS['parabola'] = parabola_from_cmd
    



