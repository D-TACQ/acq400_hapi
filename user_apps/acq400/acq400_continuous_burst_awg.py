#!/usr/bin/env python
'''
Created on 24 Sep 2020

@author: pgm

acq400_continuous_burst_awg.py UUT

load a "Rainbow" waveform and play it out

from a software point of view, it's continuous, but the waveform may run on a burst trigger
'''

import acq400_hapi
import argparse
import time

import numpy as np

# AWG "Feature"
MINBUFFERS = 4

def get_distributor_sites(args, uut):
    for dx in uut.s0.distributor.split(' '):
        (key, value) = dx.split('=')
        if key == 'sites':
            uut.sites = [ int(x) for x in value.split(',')]
            nc = 0
            for sx in uut.sites:
                nc += int(uut.modules[sx].NCHAN)
            args.nchan = nc
            print("nchan set {}".format(args.nchan))
            return
          
def configure_master_site(args, uut):
    for site in uut.sites:
        uut.modules[site].trg = '1,0,1'        
        uut.modules[site].rtm = 1 if args.burst_length > 0 else 0
        uut.modules[site].burst = '3,0,1' if args.burst_length > 0 else '0,0,0'
        uut.modules[site].rtm_translen = args.burst_length
        break
    
    
def load_burstlen_equals_wavelen(args, uut):
    # load a sequence of waveforms to be loaded and played in turn
    work=acq400_hapi.awg_data.RainbowGen(uut, args.nchan, args.length, False)
    while True:    
        for f in work.load(continuous=True):
            print("Loaded %s" % (f))
            if args.delay:
                time.sleep(args.delay)
            else:
                input("hit return for next WF")
                uut.modules[site].AWG_MODE_ABO = '1'
                uut.modules[site].playloop_length = '0'

def load_multiple_bursts_in_one_wavelen(args, uut):
    # build a sequence of bursts to load in one waveform
    work=acq400_hapi.awg_data.RainbowGen(uut, args.nchan, args.burst_length, False)
    awg = np.zeros((0, args.nchan))
    while len(awg)/args.nchan < args.length:
        for ch in range(args.nchan):
            awx = work.build(ch)
            awg = np.append(awg, awx)
            if len(awg)/args.nchan >= args.length:
                break
            
    uut.load_awg(awg.astype(np.int16), continuous=True)    
        
    input("hit return to stop")
    uut.modules[site].AWG_MODE_ABO = '1'
    uut.modules[site].playloop_length = '0'
    
                                   
def run_awg(args):
    uut = acq400_hapi.Acq400(args.uuts[0])
    get_distributor_sites(args, uut)
    
    wavelen = args.length * 2 * args.nchan
    bufferlen = int(uut.s0.bufferlen)
    if wavelen < 4 * bufferlen:
        bufferlen = args.length * 2 * args.nchan / MINBUFFERS
    uut.s0.dist_bufferlen_play = bufferlen
    uut.s0.dist_bufferlen_load = bufferlen
    
    configure_master_site(args, uut)
    
    if args.burst_length == args.length:
        load_burstlen_equals_wavelen(args, uut)
    else:
        load_multiple_bursts_in_one_wavelen(args, uut)


    
    
BURST_IS_AWGLEN = -1 
 
def run_main():
    parser = argparse.ArgumentParser(description='acq1001 awg demo')
    parser.add_argument('--length', type=int, default=8192, help="AWG length")
    parser.add_argument('--burst_length', type=int, default=BURST_IS_AWGLEN, 
        help="Burst length : {} same as AWG, 0: no burst, >0 special [sub] length".format(BURST_IS_AWGLEN))
    parser.add_argument('--delay', type=int, default=0, help="auto switch on this delay")
    parser.add_argument('--trgDX', type=int, default=0, help="trigger DX line")
    parser.add_argument('uuts', nargs=1, help="uut ")
    args = parser.parse_args()
    if args.burst_length == BURST_IS_AWGLEN:
        args.burst_length = args.length
    elif args.burst_length > 0:
        if args.burst_length > args.length:
            args.burst_length = args.length
            print("WARNING: setting burst_length equal to awg length")
    run_awg(args)
           
if __name__ == '__main__':
    run_main()
    