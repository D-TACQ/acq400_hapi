#!/usr/bin/env python3
'''
Created on 14 Aug 2023

@author: pgm
'''

import numpy as np
import argparse
import common


'''
Create a waveform with a single pulse suitable for delta coding
The pulse may also be wider than one sample for use in a absolute AWG pattern.
'''
 
def pulse(pre, width, post, amp): 
    nfull = pre + width + post  
    data = data = np.zeros(nfull)
    for ii in range(pre, pre+width):
        data[ii] = amp
    return data
        
def ui(cmd_args=None):
    pre=512
    width=1
    post=511
    amp=10
    
    parser = argparse.ArgumentParser(description="pulse", prog="pulse", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--pre', default=pre, type=int, help='Samples before pulse')
    parser.add_argument('--post', default=post, type=int, help='Samples after pulse')
    parser.add_argument('--amp',  default=amp, type=int, help='Amplitude negative values accepted')
    parser.add_argument('--width', default=width, type=int, help='Pulse Width')
    return common.ui(parser, cmd_args)

class PulseWrapper:
    def __call__(self, args):
        self.args = args
        return pulse(args.pre, args.width, args.post, args.amp)
    def __str__(self):
        args = self.args
        return f'{args.root}/pulse-x{args.reps}-{args.pre}-{args.width}-{args.post}-{args.amp}_{args.ch}.dat'

def pulse_from_cmd(cmd_args):
    return common.exec_command(ui(cmd_args), PulseWrapper())
 
# unit test: plots the data  
if __name__ == '__main__':
    data, fn = pulse_from_cmd(None)
    common.plot(data, fn)
else:
    common.WAVE_CMDS['pulse'] = pulse_from_cmd    



