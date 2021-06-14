import sys
import subprocess
import time
import acq400_hapi
import argparse
import os

def get_args():    
    parser = argparse.ArgumentParser(description='runs shots with one continuous AWG as Master and multiple UUTs using MGTDRAM')
    parser.add_argument('--aiseconds', type=int, default=10, help="number of seconds to run AI capture")
    parser.add_argument('--shots', type=int, default=1, help="number of shots to run")
    parser.add_argument('--plot', type=int, default=0, 
            help="0: no plot, OR of 1: plot raw, 2:plot gated, 4 plot first burst, 8 plot delta.")
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('uut_names', nargs='+', help="uut names")
    args = parser.parse_args()

    args.uuts = [ acq400_hapi.factory(name) for name in args.uut_names]
    for name in args.uut_names:
        os.makedirs("{}".format(name), exist_ok=True)
    return args

def run_shot(uut_names, shot, trigger):
    procs = []

    print("run_shot {}".format(shot))
    for uut in uut_names:
        f = open("{}/{:04d}.log".format(uut, shot), 'w')
        p = subprocess.Popen([ sys.executable, './user_apps/acq2106/mgtdramshot.py',
                          '--captureblocks', '800', '--offloadblocks', '800', uut ], stdout=f)
        procs.append((uut, p, f))
        print("spawned {}".format(uut))

    trigger()

    for uut, p, f in procs:
        p.wait()
        print("reaped {}".format(uut))
        f.close()

def trigger():
    time.sleep(2)
    print("trigger")



def main():
    args = get_args() 
    
    for u in args.uuts:
        u.s1.shot = 0    

    for shot in range(1, args.shots+1):
        run_shot(args.uut_names, shot, trigger)

if __name__ == '__main__':
    main()
