#!/usr/bin/env python

"""
remote command eval -e command UUT [UUT2]

usage: acq400_remote_eval.py [-h] [-s SCRIPT] [-t TRACE] uuts [uuts ...]

acq400_remote_script

positional arguments:
  uuts                  uut[s]

optional arguments:
  -h, --help            show this help message and exit
  -s SCRIPT, --script SCRIPT
                        script file [default stdin]
  -t TRACE, --trace TRACE
                        traces command execution
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
    print("WORKTODO DO NOT USE")
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

def remote_eval(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for u in uuts:
        sx, kvp = args.eval.split('.')
        kvp2 = kvp.split('=')
        key = kvp2[0]
        if len(kvp2) > 1:
            value = kvp2[1]
            cmd = 'u.svc[sx].set_knob(key, value)'
        else:
            cmd = 'u.svc[sx].get_knob(key)'
        rx = eval(cmd)
        print("{} {} => {}".format(u.uut, cmd, rx))

def run_main():
    parser = argparse.ArgumentParser(description='acq400_remote_script')
    parser.add_argument('-e','--eval', default=None, help="script file [default stdin]") 
    parser.add_argument('-s','--script', default='-', help="script file [default stdin]")     
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    args = parser.parse_args()
    if args.eval:
        remote_eval(args)
    else:
        remote_script(parser.parse_args())


# execution starts here

if __name__ == '__main__':
    run_main()
