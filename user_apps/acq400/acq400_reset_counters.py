#!/usr/bin/env python

"""
reset counters UUT [UUT2]

usage: acq400_reset_counters.py [-h] [-s sites] uuts [uuts ...]


positional arguments:
  uuts                  uut[s]

optional arguments:

"""

import sys
import acq400_hapi
import argparse
        
def reset_counters(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    sites = args.sites.split(',')
    
    for uut in uuts:
        for s in sites:
            uut.svc[s].RESET_CTR = '1'

def run_main():
    parser = argparse.ArgumentParser(description='acq400_reset_counters')
    parser.add_argument('-s','--sites', default='s0', help="sites to clear eg s0,s1,s2,cA") 
    parser.add_argument('-t','--trace', default=0, help="traces command execution")
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    reset_counters(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
