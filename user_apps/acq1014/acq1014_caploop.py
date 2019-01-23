#!/usr/bin/env python

"""
capture loop test
acq1001_caploop UUT1 [UUT2 ..]
where UUT1 is the ip-address or host name of first uut
example test client runs captures in a loop on one or more uuts

pre-requisite: UUT's are configured and ready to make a transient
capture
eg clk is running. soft trg enabled
eg transient length set.

loop continues "forever" until <CTRL-C>

usage: acq1014_caploop.py [-h] [--sleep SLEEP] [--trg TRG] [--nsam NSAM]
                          [--shots SHOTS]
                          uuts [uuts ...]

acq1014 looptest

positional arguments:
  uuts           uut pairs: m1,m2 [s1,s2 ...]

optional arguments:
  -h, --help     show this help message and exit
  --sleep SLEEP  sleep time between shots, -1:pause input
  --trg TRG      trigger int|ext
  --nsam NSAM    expected number of samples
  --shots SHOTS  number of shots to run
"""

import sys
import acq400_hapi
import argparse
import os
import numpy as np

SAVEDATA=os.getenv("SAVEDATA", None)

def save_2d_data(args, chx, nuut, nchan, shot):
     print(np.shape(chx))    
     with open("%s/DATA2D_%d.dat" % (args.save_data, shot), 'wb') as fid: 
         for uu in range(nuut):
             for cc in range(nchan):
                 chx[uu][cc].tofile(fid, '') 
                 
def run_loop(args):
    global SAVEDATA
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]             

    acq400_hapi.cleanup.init()

    if SAVEDATA:
        for u in uuts:
            u.save_data = SAVEDATA

    for uut in uuts:
        if hasattr(uut.s0, 'TIM_CTRL_LOCK'):
            print("LOCKDOWN {}".format(uut))
            uut.s0.TIM_CTRL_LOCK = 1
        uut.s1.shot='0'

    shot_controller = acq400_hapi.ShotController(uuts)
    shot = 0

    try:
        while shot < args.shots:
            if args.trg == "int":
                shot_controller.run_shot(soft_trigger=1,acq1014_ext_trigger=1)
            else:
                shot_controller.run_shot(soft_trigger=0,acq1014_ext_trigger=3)

            chx, ncol, nchan, nsam = shot_controller.read_channels()
           
            if args.save_2D:
                save_2d_data(args, chx, len(uuts), nchan, shot)
            if args.nsam > 0:
                nsam = [len(u.read_chan(1)) for u in uuts]
                err = False
                for n in nsam:
                    if n != args.nsam:
                        err = True
                print("Shot %s read_channels nsam:%d %d %s" % (uuts[0].s1.shot, nsam[0], nsam[1], 'Fail' if err else 'Pass'))
                if err:
                    break

            shot = shot + 1
            if args.sleep >= 0:
                acq400_hapi.cleanup.sleep(args.sleep)            
            else:
                print("Hit return when ready")
                sys.stdin.readline()

    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
        shot_controller.abort_shot()
    finally:        
        print("Finally, going down")    


def run_main():
    parser = argparse.ArgumentParser(description='acq1014 looptest')
    parser.add_argument('--sleep', default=1, type=int, help="sleep time between shots, -1:pause input")
    parser.add_argument('--trg', default='int', type=str, help="trigger int|ext")
    parser.add_argument('--nsam', default=0, type=int, help='expected number of samples')
    parser.add_argument('--shots', default=999999, type=int, help='number of shots to run')
    parser.add_argument('--save_data', default='DATA', type=str, help="store data to specified directory")
    parser.add_argument('--save_2D', default=1, help="store 2D data array to save_data")
    parser.add_argument('uuts', nargs='+', help="uut pairs: m1,m2 [s1,s2 ...]")
    run_loop(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()




