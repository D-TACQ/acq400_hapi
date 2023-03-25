#!/usr/bin/env python3

""" 
wait until the fleet is ready (bist0 status good), then run "preset1", amx-start-demo from CUSTOM_AMX

make sure amx-start-demo reaches the parts before accepting.

"""


import acq400_hapi
from acq400_hapi import timing
import argparse
import threading
import requests
import time


def get_parser():
    parser = argparse.ArgumentParser(description='start amx demo')
    parser.add_argument('--verbose', default=0, type=int, help='increase verbosity')
    parser.add_argument('--wrtt', default=1, help='use WRTT to start the fleet')
    parser.add_argument('uutnames', nargs='+', help="uuts")
    return parser  

def wait_bist_ok(u, args):
    url = f'http://{u.uut}/d-tacq/bist0_status'
    ii = 1
    maxi = 100
    
    while True:
        if args.verbose or ii%10 == 0:
            print(f'get {url}  {ii}/{maxi}')
            
        response = requests.get(url)
        if args.verbose:
            print(repr(response))
            
        if response.status_code == 200:
            if response.text[0] == '0':
                return True
            else:
                print(f'ERROR {u.uut} BIST FAIL')
                return False
        
        time.sleep(2.5)
        ii += 1
        if ii >= maxi:
            return False
    
    
def tee_up_action(u, args):
    print(f"hello {u.uut}")
    ok = False
    if wait_bist_ok(u, args):
        ok = True
        u.s0.preset1 = args.wrtt
        ssb = int(u.s0.ssb)
        if ssb != 128:
            print(f'ERROR {u.uut} ssb != 96 actual {ssb}')
            ok = False
        RTM_TRANSLEN = acq400_hapi.intpv(u.s1.RTM_TRANSLEN)
        rtm_translen = int(u.s1.rtm_translen)
        if RTM_TRANSLEN != 16384:
            print(f'ERROR {u.uut} {RTM_TRANSLEN} != 16384')
            ok = False
        if RTM_TRANSLEN+1 != rtm_translen:
            print(f'ERROR {u.uut}  RTM_TRANSLEN+1 != rtm_translen')
            ok = False
    u.amx_demo_ok = ok
    if args.verbose:
        print(f'u.amx_demo_ok set {ok}')
    
def tee_up_mt_action(u, args):
    def _tee_up_mt_action():
        tee_up_action(u, args)
    return _tee_up_mt_action

@timing 
def tee_up_mt(args):
    thx = []
    for u in args.uuts:
        u.amx_demo_ok = False
        th = threading.Thread(target=tee_up_mt_action(u, args))
        th.start()
        thx.append(th)
    
    for t in thx:
        t.join()
        
    for u in args.uuts:
        if not u.amx_demo_ok:
            print(f"ERROR: {u.uut} is NOT OK")
             

@timing 
def connect(args):
    args.uuts = [ acq400_hapi.Acq2106(u, has_comms=False, has_wr=True) for u in args.uutnames ]
    
def run_main(args):
    connect(args)
    tee_up_mt(args)
    
if __name__ == '__main__':
    run_main(get_parser().parse_args())
 