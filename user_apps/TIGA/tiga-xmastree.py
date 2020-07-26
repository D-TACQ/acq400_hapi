#!/usr/bin/env python

""" tiga-xmastree.py : bumper TIGA exercise.

* Connect a 1Hz trigger to site 2 TRGIN on UUT1
* With multiple UUT's, they will all respond to the same trigger at the same time.

"""


import acq400_hapi
import os
import argparse
import sys


def _in_tolerance(y1, y2):
    return y1-y2 < 3 or y2/y1 > 0.9  
           
def in_tolerance(y1, y2):
    if y1 >= y2:
        return _in_tolerance(y1, y2)
    else:
        return _in_tolerance(y2, y1)
   
   
class test_exec(object):

    def __init__(self, f):
        """
        If there are no decorator arguments, the function
        to be decorated is passed to the constructor.
        """
        #print("Inside __init__()")
        self.f = f

    def __call__(self, *args):
        """
        The __call__ method is not called until the
        decorated function is called.
        """
        print("\n\nTEST: {}".format(self.f.__name__))
        self.f(*args)
        while True:
            rc = input("continue Y/n")
            if len(rc) == 0:
                rc = 'Y'
            if rc == 'Y':
                break
            if rc == 'N' or rc == 'n' or rc == 'q':
                sys.exit(1)

        
@test_exec        
def set_clkout(uut):
    print("\nCLKOUT TEST")
    clkout_freqs = {}
    for tx, site in enumerate(uut.pg_sites):
        sx = uut.modules[site]
        if tx == 0:
            print("run site {} at max output 250/10 = 25MHz")
            sx.CLK = 'external'
            sx.CLK_DX = 'd0'
            sx.CLK_SENSE = 'rising'
            sx.CLKDIV = '10'
            clkout_freqs[site] = 25e6
        if tx == 1:
            print("run_site {} at output 1MHz".format(site))
            sx.CLK = 'external'
            sx.CLK_DX = 'd1'
            sx.CLK_SENSE = 'rising'
            sx.CLKDIV = '10'
            clkout_freqs[site] = 1e6
        if tx == 2:
            print("chain site {} from left hand site at output 1kHz".format(site))
            sx.CLK = 'external'
            sx.CLK_DX = 'd{}'.format(site-1+1)
            sx.CLK_SENSE = 'rising'
            sx.CLKDIV = '1000'
            clkout_freqs[site] = 1e3
        if tx == 3:
            print("chain site {} from left hand site at output 1Hz".format(site))
            sx.CLK = 'external'
            sx.CLK_DX = 'd{}'.format(site-1+1)
            sx.CLK_SENSE = 'rising'
            sx.CLKDIV = '1000'
            clkout_freqs[site] = 1           
    
    
    for site in clkout_freqs.keys():
        setpoint = float(clkout_freqs[site])
        actual = float(uut.svc['s0'].get_knob("SIG_CLK_S{}_FREQ".format(site)).split()[1])
        print("site:{} set:{:8.3e} actual:{:8.3e} {}".format(site, setpoint, actual, 
                            "PASS" if in_tolerance(setpoint, actual) else "FAIL"))
        
@test_exec         
def run_pg_cascade_trgin(uut): 
    print("\nTRGIN TEST")
    for tx, site in enumerate(uut.pg_sites):
        sx = uut.modules[site]
        if tx == 0:
            print("trigger from local TRGIN")
            sx.TRG = 'enable'
            sx.TRG_DX = 'TRGIN'
            sx.TRG_SENSE = 'rising'
            sx.TRGOUT = 'PGIDX'
            
            
        if tx == 1:
            print("run_site {} with cascade trigger from LH site".format(site))
            sx.TRG = 'enable'
            sx.TRG_DX = 'd{}'.format(site-1+1)
            sx.TRG_SENSE = 'rising'
            sx.TRGOUT = 'PGIDX'
            
            
        if tx == 2:
            print("chain site {} with cascade trigger from LH site".format(site))
            sx.TRG = 'enable'
            sx.TRG_DX = 'd{}'.format(site-1+1)
            sx.TRG_SENSE = 'rising'
            sx.TRGOUT = 'PGIDX'
            
            
        if tx == 3:
            print("chain site {} with cascade trigger from LH site".format(site))
            sx.TRG = 'enable'
            sx.TRG_DX = 'd{}'.format(site-1+1)
            sx.TRG_SENSE = 'rising'
            sx.TRGOUT = 'PGIDX'
            
        
"""
     
     # todo now load a 4 x 1s sequence with PG4 trigger at the end of each second.
# TIGA sings a round..
# in the style of "partridge in a pear tree"

STL sets up a series of 1s cycles, with d4 INDEX->TRG at fires at end of each second

CYCLE,d3,d2,d1,d0      # flashes in second
1 1,0,0,0
2 1,2,0,0
3 1,2,3,0
4 1,2,3,4

Load all sites.
PG2 triggers on SOFT_TRIGGER
PG3,4,5 trigger on SITE-1 TRG

CYCLE PG2 PG3 PG4 PG5
1 1,0,0,0 0,0,0,0 0,0,0,0 0,0,0,0
2 1,2,0,0 1,0,0,0 0,0,0,0 0,0,0,0
3 1,2,3,0 1,2,0,0 1,0,0,0 0,0,0,0
4 1,2,3,4 1,2,3,0 1,2,0,0 1,0,0,0

5 1,0,0,0 1,2,3,4 1,2,3,0 1,2,0,0
6 1,2,0,0 1,0,0,0 1,2,3,4 1,2,3,0
7 1,2,3,0 1,2,0,0 1,0,0,0 1,2,3,4
8 1,2,3,4 1,2,3,0 1,2,0,0 1,0,0,0


"""      
 
@test_exec   
def run_local_wrtt(uut):
    for tx, site in enumerate(uut.pg_sites):
        sx = uut.modules[site]
        if tx == 0:
            print("trigger {} from local WRTT".format(site))
            sx.TRG_DX = 'WRTT'
            sx.WRTD_TX_MASK = 1<<(site+1)
            sx.wrtd_commit_tx=1                 

@test_exec 
def run_local_wrtt_allsites(uut):
    for tx, site in enumerate(uut.pg_sites):
        sx = uut.modules[site]
        sx.TRG_DX = 'WRTT'
        if tx == 0:
            sx.WRTD_TX_MASK = 0xfc
            sx.wrtd_commit_tx=1        
@test_exec             
def run_global_wrtt_allsites(uut):
    for tx, site in enumerate(uut.pg_sites):
        sx = uut.modules[site]
        sx.TRG_DX = 'd0'
        if tx == 0:
            sx.WRTD_TX_MASK = 1
            sx.wrtd_commit_tx=1   
    uut.s0.SIG_SRC_TRG_0 = 'WRTT0'     
    

def xmas_tree(args, uut):
    for test in [ set_clkout, run_pg_cascade_trgin, run_local_wrtt, run_local_wrtt_allsites, run_global_wrtt_allsites]:
        test(uut)
    
    
    
def xmas_forest(args):
    for u in args.uuts:
        xmas_tree(args, u)
    
    
def main():
    parser = argparse.ArgumentParser(description='tiga-xmastree')
    parser.add_argument('uut', nargs='+', help="uuts")
    args = parser.parse_args()
    args.uuts = [ acq400_hapi.Acq2106_TIGA(u) for u in args.uut ]
    xmas_forest(args)
    
if __name__ == '__main__':
    main()