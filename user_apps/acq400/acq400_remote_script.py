#!/usr/bin/env python

""" remote scripting -f scriptfile UUT [UUT2]
"""

import sys
import acq400_hapi
import argparse


def handle_line(uuts, line):
    if len(line) <= 1 or line.startswith('#'):
        return
    for uut in uuts:
        uut.s0.sr(line)
        
def remote_script(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]
    
    if args.trace:
        for uut in uuts:
            uut.s0.trace = args.trace
    
    if args.script == '-':
        for line in sys.stdin:            
            handle_line(uuts, line)
    else:
        with open(args.script) as f:
            for line in f:                
                handle_line(uuts, line)

def run_main():
    parser = argparse.ArgumentParser(description='acq400_remote_script')
    parser.add_argument('-s','--script', default='-', help="script file [default stdin]") 
    parser.add_argument('-t','--trace', default=0, help="traces command execution")
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    remote_script(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
