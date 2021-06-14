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
    parser.add_argument('uut_names', nargs='+', help="uut names")
    args = parser.parse_args()

    args.uuts = [ acq400_hapi.factory(name) for name in args.uut_names]
    for name in args.uut_names:
        os.makedirs("{}".format(name), exist_ok=True)
    if args.mu:
        args.mu = acq400_hapi.factory(args.mu)

    return args

procs = []

@timing
def run_shot(args, uut_names, shot, trigger):
    procs.clear()
    print("run_shot {}".format(shot))
    for uut in uut_names:
        f = open("{}/{:04d}.log".format(uut, shot), 'w')
        p = subprocess.Popen([ sys.executable, './user_apps/acq2106/mgtdramshot.py',
                          '--captureblocks', '800', '--offloadblocks', '800', uut ], stdout=f)
        procs.append((uut, p, f))
        print("spawned {}".format(uut))

    trigger(args)
    monitor(args)

    for uut, p, f in procs:
        p.wait()
        print("reaped {}".format(uut))
        f.close()

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
def monitor(args):
    idle = np.array([0] * len(args.uuts))
    runs = 0
    while True:
        time.sleep(1)
        runs += 1
        print("{:3d}:".format(runs), end='')
        for ix, uut in enumerate(args.uuts):
            cs = uut.s0.cstate
            cstate = cs.split(' ')[0]
            idle[ix] = int(cstate)
            print("{} {},".format(uut.uut, cs), end='')
        print("")
        if np.all(idle) == 0:
            break

    


def main():
    args = get_args() 
    
    for u in args.uuts:
        u.s1.shot = 0    

    for shot in range(1, args.shots+1):
        run_shot(args, args.uut_names, shot, trigger)

if __name__ == '__main__':
    main()
