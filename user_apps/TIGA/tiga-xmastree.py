#!/usr/bin/env python

""" tiga-xmastree.py : bumper TIGA exercise.

* Connect a 1Hz trigger to site 2 TRGIN on UUT1
* With multiple UUT's, they will all respond to the same trigger at the same time.

"""


import acq400_hapi
import os
import argparse


def _in_tolerance(y1, y2):
    return y1-y2 < 3 or y2/y1 > 0.9  
           
def in_tolerance(y1, y2):
    if y1 >= y2:
        return _in_tolerance(y1, y2)
    else:
        return _in_tolerance(y2, y1)
    
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
            print("run_site {} at output 1MHz")
            sx.CLK = 'external'
            sx.CLK_DX = 'd1'
            sx.CLK_SENSE = 'rising'
            sx.CLKDIV = '10'
            clkout_freqs[site] = 1e6
        if tx == 2:
            print("chain site {} from left hand site at output 1kHz")
            sx.CLK = 'external'
            sx.CLK_DX = 'd{}'.format(site-1+1)
            sx.CLK_SENSE = 'rising'
            sx.CLKDIV = '1000'
            clkout_freqs[site] = 1e3
        if tx == 3:
            print("chain site {} from left hand site at output 1Hz")
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
        
        
            

def xmas_tree(args, uut):
    set_clkout(uut)
    
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