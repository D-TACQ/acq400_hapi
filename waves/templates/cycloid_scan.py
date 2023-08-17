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
1. ramp north from A0 to A1 in Tramp
2. decelerate north to 0 from ww
3. accelerate  south from 0 to ww
4. ramp south from A1 to A0 in Tramp
5. decelerate south from ww to 0
6. accelerate north from 0 to ww
'''
def cycloid_scan(nramp, A0, A1, nrs, alpha):
    print(f'cycloid scan {nramp} {A0} {A1} {nrs} {alpha}')
    nfull = nramp + nrs + nramp + nrs
    print(f'nfull {nfull}')
    data = np.zeros(nfull)
    AA = A1-A0
    ww = AA/nramp
    acc = (ww*ww)/(2*alpha)
    
    print(f'AA:{AA} ww:{ww} acc:{acc}')
    
    ii = 0
    # 1. ramp north from A0 to A1 in Tramp
    for ii2 in range(0, nramp):
        data[ii] = A0 + ii2 * ww
        ii += 1
    # 2. decelerate north to 0 from ww
    uu = ww
    s0 = data[ii-1]
    for ii2 in range(0, nrs//2):        
        data[ii] = s0 + uu - acc*(1*1)/2
        #print(f's0:{s0} uu:{uu} data[ii]:{data[ii]}')
        if uu > 0:
            uu -= acc
        else:
            uu = 0
        s0 = data[ii]
        ii += 1
        
        
    # 3. accelerate  south from 0 to ww   
    for ii2 in range(0, nrs//2):
        data[ii] = data[ii-2*ii2-1]
        ii += 1
    # 4. ramp south from A1 to A0 in Tramp
    ww = -AA/nramp    
    for ii2 in range(0, nramp):
        data[ii] = A1 + ii2 * ww
        ii += 1
    # 5. decelerate south from ww to 0
    acc = -(ww*ww)/(2*alpha)
    uu = ww
    s0 = data[ii-1]
    for ii2 in range(0, nrs//2):
        data[ii] = s0 + uu - acc*(1*1)/2
        if uu < 0:
            uu -= acc
        else:
            uu = 0
        s0 = data[ii]
        ii += 1
    # 6. accelerate north from 0 to ww  
    for ii2 in range(0, nrs//2):
        data[ii] = data[ii-2*ii2-1]
        ii += 1
        
    return data    
    
def ui(cmd_args=None):
    nramp = 512
    A0 =  1000
    A1 = 11000
    nrs = 256
    alpha = 1200
    
    parser = argparse.ArgumentParser(description="cycloid_scan", prog="cycloid_scan", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--nramp', default=nramp, type=int, help='nramp proxy for Tramp')
    parser.add_argument('--A0', default=A0, type=int, help='AO: start position')
    parser.add_argument('--A1', default=A1, type=int, help='A1: end position')
    parser.add_argument('--nrs', default=nrs, type=int, help='nrs: proxy for Trs')
    parser.add_argument('--alpha', default=alpha, type=int, help='alpha: distance covered to deceleration end point')
    return common.ui(parser, cmd_args)

class CycloidWrapper:
    def __call__(self, args):
        self.args = args
        return cycloid_scan(args.nramp, args.A0, args.A1, args.nrs, args.alpha)
    def __str__(self):
        args = self.args
        return f'{args.root}/cycloid-{args.nramp}-{args.A0}-{args.A1}-{args.nrs}-{args.alpha}_{args.ch}.dat'
        
def cycloid_from_cmd(cmd_args):
    return common.exec_command(ui(cmd_args), CycloidWrapper())

# unit test: plots the data  
if __name__ == '__main__':
    data, fn = cycloid_from_cmd(None)
    common.plot(data, fn)
else:
    common.WAVE_CMDS['cycloid_scan'] = cycloid_from_cmd 



