#!/usr/bin/env python

"""reset uut counters"""

import sys
import acq400_hapi
import argparse
import threading


def cs(uut):
    return acq400_hapi.factory
        
def reset1(uut, s):
    try:
        uut.svc[s].RESET_CTR = '1'
        print("reset {} {} done".format(uut.uut, s))
    except KeyError:
        print("WORKTODO KeyError {}")

def reset_counters_threaded(args):
    uuts = [cs(u) for u in args.uuts]
    sites = args.sites.split(',')
#    printr(sites)
    threads = []
    for uut in uuts:
        for s in sites:                       
            t = threading.Thread(target=reset1, args=(uut, s))
            threads.append(t)
            t.start()
             
    for t in threads:
        t.join()
            
            
def reset_counters_serial(args):
    uuts = [cs(u) for u in args.uuts]
    sites = args.sites.split(',')
#    printi(sites)
    
    for uut in uuts:
        for s in sites:
            reset1(uut, s)
  
def reset2(uutname, sites):
    uut = cs(uutname)
    for s in sites:
        reset1(uut, s)
        
def reset_counters_threaded_ultra(args):    
    sites = args.sites.split(',')
#    print(sites)
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

def get_parser():
    parser = argparse.ArgumentParser(description='acq400_reset_counters')
    parser.add_argument('-s','--sites', default='s0', help="sites to clear eg s0,s1,s2,cA") 
    parser.add_argument('-t','--trace', default=0, help="traces command execution")
    parser.add_argument('--threaded', type=int, default=2)
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    return parser

if __name__ == '__main__':
    reset_counters(get_parser().parse_args())
