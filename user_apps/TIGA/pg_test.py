#!/usr/bin/env python
'''
pg_test : loads pg with STL and starts. remotable version of CARE/pg_test
Created on 17 Aug 2021

@author: pgm

usage: pg_test.py [-h] [--site SITE] [--mode MODE] [--tscale TSCALE] [--stl STL] [--stl_trace STL_TRACE] uut [uut ...]

pg_test

positional arguments:
  uut                   uuts

optional arguments:
  -h, --help            show this help message and exit
  --site SITE           list of sites eg 5,6 to load
  --mode MODE           ONCE, LOOP, LOOPWAIT
  --tscale TSCALE       set gpg_timescaler
  --stl STL             canned stl 1,2 or @file, possible entry per site
  --stl_trace STL_TRACE
                        trace stl load

SITECLIENT_TRACE=1 ./user_apps/TIGA/pg_test.py --site=5,6 --stl=2 --tscale=4000 acq2106_315

eg load 5 and 6 with pattern 2

SITECLIENT_TRACE=1 ./user_apps/TIGA/pg_test.py --site=5,6 --stl=1,2 --tscale=4000 acq2106_315

eg load 5 with pattern 1 and 6 with pattern 2

SITECLIENT_TRACE=1 ./user_apps/TIGA/pg_test.py --site=5,6 --stl=@mypattern.stl -tscale=40 acq2106_315

eg load 5 and 6 with the stl from mypattern.stl, scale by 40 eg
useful if mypattern.stl is scaled in usecs and the PGCLK is 40MHz..

'''
import acq400_hapi
import os
import argparse
import sys

STL = (    
"",

#index from 1    
"""
10,1
20,0
30,2
40,0
50,4
60,0
70,1f
80,1
90,0
""",

"""
10,1
20,2
30,4
40,8
50,10
60,0
""",
)

def get_stl(fname):
    with open (fname, "r") as stl_file:
        stl = stl_file.read()
    return stl
    
def get_args():
    parser = argparse.ArgumentParser(description='pg_test')
    parser.add_argument('--site', default='6', help="list of sites eg 5,6 to load")
    parser.add_argument('--mode', default='ONCE', help='ONCE, LOOP, LOOPWAIT')
    parser.add_argument('--tscale', default=None, help='set gpg_timescaler')
    parser.add_argument('--stl', default=1, help='canned stl 1,2 or @file, possible entry per site')
    parser.add_argument('--stl_trace', default=0, help='trace stl load')
    parser.add_argument('--trg', default='1,0,1', help='set trigger, default WRTT0, NOTOUCH to leave it')
    parser.add_argument('uut', nargs='+', help="uuts")
    args = parser.parse_args()
    args.sites = [ int(x) for x in args.site.split(',') ]
    args.stl = args.stl.split(',')
    args.STL = {}
    for ix, stl in enumerate(args.stl):
        if stl.startswith('@'):
            args.STL[args.sites[ix]] = get_stl(stl[1:])
        elif stl.isnumeric():            
            stl = int(stl)
            if stl >= 1 and stl < len(STL):
                args.STL[args.sites[ix]] = STL[stl]        
        else:
            print("WORKTODO for stl {}".format(stl))
    
    # ensure there is an STL for every site, either default STL[1] or previous site STL
    s0 = 0
    for s1 in args.sites:
        if s1 not in args.STL:
            if s0 == 0:
                args.STL[s1] = STL[1]
            else:
                 args.STL[s1] = args.STL[s0]
        s0 = s1
    return args

def pg_test1(args, uut, site):
    site_svc = uut.svc['s{}'.format(site)]
    site_svc.GPG_ENABLE = 0
    if args.trg != 'NOTOUCH':
        site_svc.trg = args.trg
    if args.tscale:
        site_svc.gpg_timescaler = int(args.tscale)
    uut.load_dio482pg(site, args.STL[site], trace=args.stl_trace)
    site_svc.GPG_MODE = args.mode
    mode_rb = acq400_hapi.Acq400.pv(site_svc.GPG_MODE)
    if mode_rb != args.mode:
        print("WARNING: specified mode '{}' rejected, currently set '{}'".format(args.mode, mode_rb))
    site_svc.GPG_ENABLE = 1
    
    
    
def pg_test(args):
    uuts = [ acq400_hapi.factory(u) for u in args.uut ]
    for u in uuts:
        for s in args.sites:
            pg_test1(args, u, s)


def main():
    pg_test(get_args())

if __name__ == '__main__':
    main()