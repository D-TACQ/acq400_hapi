#!/usr/bin/env python

"""acq400_remote_script"""

import sys
import acq400_hapi
import argparse
import re

back_compat = re.compile('[sg]et.site ([0-9]+) ')

def remote_eval(uuts, expr):
    for u in uuts:
        m = back_compat.match(expr)
        if m:
            expr = re.sub(back_compat, 's{}.'.format(m.group(1)), expr)
       
        sx, kvp = expr.split('.')
        kvp2 = kvp.split('=')
        key = kvp2[0]
        if len(kvp2) > 1:
            value = kvp2[1]
            cmd = 'u.svc[sx].set_knob(key, value)'
            txt = '{}.{}={} st:'.format(sx, key, value)
        else:
            cmd = 'u.svc[sx].get_knob(key)'
            txt = '{}.{}'.format(sx, key)
        rx = eval(cmd)
        print("{}:{} => {}".format(u.uut, txt, rx))
   
def handle_line(uuts, line):
    if len(line) <= 1 or line.startswith('#'):
        return
    remote_eval(uuts, line)
                
def remote_script(uuts, script):
    if script == '-':
        print("remote_script from stdin")
        for line in sys.stdin:            
            handle_line(uuts, line.strip())
    else:
        with open(script) as f:
            for line in f:                
                handle_line(uuts, line.strip()) 
 
def remote_script_by_uut(uuts, script):
    for u in uuts:
         with open(script) as f:
            for line in f:                
                handle_line((u,), line.strip())                 
                    

def run_main(args):
    uuts = [acq400_hapi.factory(u) for u in args.uuts]
    if args.eval:
        remote_eval(uuts, args.eval)
    elif args.script_by_uut:
        remote_script_by_uut(uuts, args.script_by_uut)
    else:
        remote_script(uuts, args.script)


def get_parser():
    parser = argparse.ArgumentParser(description='acq400_remote_script')
    parser.add_argument('-e','--eval', default=None, help="script file [default stdin]") 
    parser.add_argument('-s','--script', default='-', help="script file [default stdin]")
    parser.add_argument('--script_by_uut', default=None, help="script file [default stdin]")        
    parser.add_argument('uuts', nargs='+', help="uut[s]")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
