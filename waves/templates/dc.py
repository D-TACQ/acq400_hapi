#!/usr/bin/env python3
'''
Created on 14 Aug 2023

@author: pgm
'''

import numpy as np
import argparse
import common


'''
Create a waveform with a single dc value
'''
 
def dc(nsamples, offset): 
    data = data = np.zeros(nsamples) + offset
    return data
        
def ui(cmd_args=None):
    nsam=1
    offset=1
    
    parser = argparse.ArgumentParser(description='dc', prog='dc', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--nsam', default=nsam, type=int, help='nsam: samples waveform')
    parser.add_argument('--offset',  default=offset, type=int, help='Offset negative values accepted')
    return common.ui(parser, cmd_args)

class DCWrapper:
    def __call__(self, args):
        self.args = args
        return dc(args.nsam, args.offset)
    def __str__(self):
        args = self.args
        return f'{args.root}/dc-{args.nsam}-{args.offset}_{args.ch}.dat'

def dc_from_cmd(cmd_args):
    return common.exec_command(ui(cmd_args), DCWrapper())

# unit test: plots the data  
if __name__ == '__main__':
    data, fn = dc_from_cmd(None)
    common.plot(data, fn)
else:
    common.WAVE_CMDS['dc'] = dc_from_cmd
    



