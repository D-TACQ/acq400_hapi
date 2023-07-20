#!/usr/bin/env python3
'''
Created on 20 Jul 2023

@author: pgm
'''

import numpy as np
import matplotlib.pyplot as plt
import argparse

ES_MAGIC    = 0xaa55f154
ES_SAMPLE   = 4
ES_CLK      = 5
ES_SAMPLE2  = 6
ES_CLK2     = 7

def analyse_es(args, raw_es):
    print(f'raw_es.shape:{raw_es.shape}')
    esx = np.nonzero(raw_es[:,0] == ES_MAGIC)
    print(f'type esx {type(esx)}')
    
    valid_es = []
    for ix in esx[0]:
#        print(f'ix={ix}')
        es = raw_es[ix,:]
#        print(f'es.shape:{es.shape}')
        with np.printoptions(formatter={'int':hex}):
            print(es)        
        if es[0] == ES_MAGIC and es[1] == ES_MAGIC and es[2] == ES_MAGIC and es[3] == ES_MAGIC:
            if es[ES_SAMPLE] == es[ES_SAMPLE2] and es[ES_CLK] == es[ES_CLK2]:
                valid_es.append((ix, es[ES_SAMPLE], es[ES_CLK]))
                continue
            
        print(f"Warning: invalid es at {ix}")
        
    delta_es = 0
    delta_sample = 0
    delta_clk = 0
       
    print(f'{"index":>10},{"sample":>10},{"clockcount":>10},{"d_index":>10},{"d_sample":>10},{"d_clockcount":>10}')
    es = valid_es[0]
    print(f'{es[0]:>10},{es[1]:>10},{es[2]:>10},{delta_es:>10},{delta_sample:>10},{delta_clk:>10}')
    es1 = es
    for es in valid_es[1:]: 
        delta_es = es[0] - es1[0]
        delta_sample = es[1] - es1[1]
        delta_clk = es[2] - es1[2]
        print(f'{es[0]:>10},{es[1]:>10},{es[2]:>10},{delta_es:>10},{delta_sample:>10},{delta_clk:>10}')
        es1 = es
    
    
def analyse(args):
    fname = args.data[0]
    raw_adc = np.fromfile(fname, dtype=args.np_data_type)
    ll = len(raw_adc)//args.nchan
    raw_adc = raw_adc[0:ll*args.nchan]
    raw_es = raw_adc.view(np.uint32)
    
    raw_adc = np.reshape(raw_adc, (ll, args.nchan))
    raw_es  = np.reshape(raw_es,  (ll, args.ess))
    
    print(f"raw_adc {raw_adc.shape}")
    print(f"raw_es  {raw_es.shape}")
    analyse_es(args, raw_es)
    return (raw_adc, raw_es)

def get_parser():
    parser = argparse.ArgumentParser(description='rgm plot demo')
    parser.add_argument('--nchan', type=int, default=32)
    parser.add_argument('--data_type', type=int, default=None, help='Use int16 or int32 for data demux.')
    parser.add_argument('data', nargs=1, help="data ")
    return parser
 
def fix_args(args):
    if args.data_type == 16:
        args.np_data_type = np.int16
        args.WSIZE = 2
        args.ess = args.nchan//2
    elif args.data_type == 8:
        args.np_data_type = np.int8
        args.WSIZE = 1
        rgs.ess = args.nchan//4
    else:
        args.np_data_type = np.int32
        args.WSIZE = 4
        args.ess = args.nchan
    args.ssb = args.nchan * args.WSIZE
    return args

   
def run_main():
    analyse(fix_args(get_parser().parse_args()))

# execution starts here

if __name__ == '__main__':
    run_main()