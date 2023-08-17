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

def dc_from_cmd(cmd_args):
    args = ui(cmd_args)
    if not args:
        return None, None
    data = dc(args.nsam, args.offset)
    if args.root != './':
        os.makedirs(args.root, exist_ok=True)
    root = args.root
    if root[-1] == '/':
        root = root[:-1]
    fn = f'{root}/dc-{args.nsam}-{args.offset}_{args.ch}.dat'
    data.astype(np.int16).tofile(fn)
    print(f'saved as {fn}')
    return data, fn

# common interface
def cmd(cmd_args):    
    return dc_from_cmd(cmd_args)
 
# unit test: plots the data  
if __name__ == '__main__':
    data, fn = dc_from_cmd(None)
    common.plot(data, fn)
else:
    common.WAVE_CMDS['dc'] = cmd
    



