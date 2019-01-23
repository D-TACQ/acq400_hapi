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
import threading


        
def reset1(uut, s):
    uut.svc[s].RESET_CTR = '1'
    print "reset {} {} done".format(uut.uut, s)

def reset_counters_threaded(args):
    uuts = [acq400_hapi.Acq2106(u) for u in args.uuts]
    sites = args.sites.split(',')
    print sites
    threads = []
    for uut in uuts:
        for s in sites:                       
            t = threading.Thread(target=reset1, args=(uut, s))
            threads.append(t)
            t.start()
             
    for t in threads:
        t.join()
            
            
def reset_counters_serial(args):
    uuts = [acq400_hapi.Acq2106(u) for u in args.uuts]
    sites = args.sites.split(',')
    print sites
    
    for uut in uuts:
        for s in sites:
            reset1(uut, s)
  
def reset2(uutname, sites):
    uut = acq400_hapi.Acq2106(uutname)
    for s in sites:
        reset1(uut, s)
        
def reset_counters_threaded_ultra(args):    
    sites = args.sites.split(',')
    print sites
    threads = []
    for uutname in args.uuts:                      
        t = threading.Thread(target=reset2, args=(uutname, sites))
        threads.append(t)
        t.start()
             
    for t in threads:
        t.join()
  
def reset_counters(args):
    if args.threaded > 1:
        reset_counters_threaded_ultra(args)
    elif args.threaded:     
        reset_counters_threaded(args)
    else:
        reset_counters_serial(args)

def run_main():
    parser = argparse.ArgumentParser(description='acq400_reset_counters')
    parser.add_argument('-s','--sites', default='s0', help="sites to clear eg s0,s1,s2,cA") 
    parser.add_argument('-t','--trace', default=0, help="traces command execution")
    parser.add_argument('--threaded', type=int, default=2)
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    reset_counters(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
