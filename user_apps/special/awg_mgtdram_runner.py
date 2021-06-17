#!/usr/bin/env python3
'''
assuming a system with 1 x AWG, 2+ x AI, run shots and offload the data
'''
import sys
import subprocess
import time
import acq400_hapi
import argparse
import os
import numpy as np

from functools import wraps

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print('TIMING:func:%r took: %2.2f sec' % (f.__name__, te-ts))
        return result
    return wrap

def get_args():    
    parser = argparse.ArgumentParser(description='runs shots with one continuous AWG as Master and multiple UUTs using MGTDRAM')
    parser.add_argument('--aiseconds', type=int, default=10, help="number of seconds to run AI capture")
    parser.add_argument('--shots', type=int, default=1, help="number of shots to run")
    parser.add_argument('--plot', type=int, default=0, 
            help="0: no plot, OR of 1: plot raw, 2:plot gated, 4 plot first burst, 8 plot delta.")
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--mu', help="master uut, for trigger")
    parser.add_argument('--nbufs', default=800, type=int, help="number of 4MB buffers to capture")
    parser.add_argument('--shot_seconds', default=None, type=int, help="specify shot duration in seconds. Overwrites --nbufs")
    parser.add_argument('--awg_restart', default=1, type=int, help="force awg restart for constant phase")
    parser.add_argument('--save_egu', default=0, type=int, help="save data in engineering units")
    parser.add_argument('uut_names', nargs='+', help="uut names")
    args = parser.parse_args()

    args.uuts = [ acq400_hapi.factory(name) for name in args.uut_names]
    for name in args.uut_names:
        os.makedirs("{}".format(name), exist_ok=True)
    if args.mu:
        args.mu = acq400_hapi.factory(args.mu)

    if args.shot_seconds:
        set_shot_seconds(args)
    return args

procs = []

def set_shot_seconds(args):
    ssb = int(args.uuts[0].s0.ssb)
    fs = int(acq400_hapi.Acq400.freq(args.uuts[0].s0.SIG_CLK_S1_FREQ))
    mbps = fs*ssb/1000000
    nbufs = int(mbps*args.shot_seconds//4)
    nbufs += 16
    if nbufs >= 2000:
        nbufs = 2000
    print("fs:{} ssb:{} MBPS:{} nbufs:{}".format(ssb, fs, mbps, nbufs))
    args.nbufs = nbufs
    
    
@timing
def run_shot(args, uut_names, shot, trigger):
    print("\nrun_shot {}\n".format(shot))
    
    if args.awg_restart:
        restart_awg(args)
            
    procs.clear()
    
    for uut in uut_names:
        f = open("{}/{:04d}.log".format(uut, shot), 'w')
        p = subprocess.Popen([ sys.executable, './user_apps/acq2106/mgtdramshot.py',
                          '--captureblocks', str(args.nbufs), '--offloadblocks', str(args.nbufs), uut ], stdout=f)
        procs.append((uut, p, f))
        print("spawned {}".format(uut))

    trigger(args)
    capture_monitor(args)
    offload_monitor(args)

    for uut, p, f in procs:
        p.wait()
        print("reaped {}".format(uut))
        f.close()
        
    if args.save_egu:
        save_egu(args)


@timing
def restart_awg(args):
    if not args.mu:
        print("ERROR: master unit not defined")
        sys.exit(1)
    
    playloop_length = int(args.mu.s1.playloop_length.split(' ')[0])
    if playloop_length == 0:
        print("WARNING: AWG not setup")
    else:
        args.mu.s1.AWG_MODE_ABO = '1'
        time.sleep(1)
        while acq400_hapi.Acq400.intpv(args.mu.s1.AWG_MODE_ABO) == 1:
            time.sleep(0.2)            
        args.mu.s1.playloop_length = '0'
        time.sleep(0.1)        
        args.mu.s1.playloop_length = '{} 0'.format(playloop_length)

@timing
def trigger(args):
    for u in args.uuts:
        armed = False
        while not armed:
            cstate = u.s0.cstate.split(' ')[0]
            if cstate == '1':
                armed = True
                print("{} ARMED".format(u.uut))
            elif cstate == '0':
                time.sleep(0.3)
            else:
                print("{} ERROR BAD STATE {}".format(u.uut, cstate))
                sys.exit(1)
                
    if args.mu:
        print("{} trigger".format(args.mu.uut))
        args.mu.s0.soft_trigger = '1'
    else:
        print("trigger")
@timing
def offload_monitor(args):
    idle = np.array([0] * len(args.uuts))
    runs = 0

    print("Offload Monitor")
    print("{:>3} {:8} {}".format('s', 'uut', 'pull buffers'))

    while True:
        time.sleep(2)
        runs += 2
        print("{:3d}:".format(runs), end='')
        for ix, uut in enumerate(args.uuts):
            npull = acq400_hapi.Acq400.intpv(uut.cA.SIG_MGT_PULL_BUFS_COUNT)
            idle[ix] = 1 if npull > (args.nbufs-64) else 0
            print("{:11} {:3d}".format(uut.uut, npull), end=', ' if ix < len(args.uuts)-1 else '\n')
        if np.all(idle) == 1:
            break

@timing
def capture_monitor(args):
    idle = np.array([0] * len(args.uuts))
    runs = 0
    print("Capture Monitor")
    print("{:>3}:{:11} {} {:8}".format('s', 'uut', 'S', 'samples s:seconds, S:state'))

    while True:
        time.sleep(1)
        runs += 1
        print("{:3d}:".format(runs), end='')
        for ix, uut in enumerate(args.uuts):
            cs = uut.s0.cstate.split(' ')
            idle[ix] = int(cs[0])
            print("{:11} {:1} {:8d}".format(uut.uut, cs[0], int(cs[3])), end=', ' if ix < len(args.uuts)-1 else '\n')
        if np.all(idle) == 0:
            break
    

def save_egu1(uut, shot, rawfile):
    nchan = int(uut.s0.NCHAN)
    raw = np.fromfile(rawfile, np.int16).reshape(-1, nchan)
    volts = np.zeros(len(raw)*nchan).reshape(-1, nchan)
    for ch in range(1, nchan+1):
        volts[:,ch-1] = uut.chan2volts(ch, raw)
    
    npfile = re.sub(r'\.dat', r'\.volts', rawfile)
    with open(npfile, "wb") as vp:
        volts.tofile(vp) 
    
        
@timing 
def save_egu(args):
    for uut in args.uuts:
        shot = int(uut.s1.shot)
        save_egu1(uut, shot, "{}/{:04d}.dat".format(uut.uut, shot))

def main():
    args = get_args() 
    
    for u in args.uuts:
        u.s1.shot = 0
    if args.mu:
        args.mu.s1.shot = 0    

    for shot in range(1, args.shots+1):
        run_shot(args, args.uut_names, shot, trigger)

if __name__ == '__main__':
    main()
