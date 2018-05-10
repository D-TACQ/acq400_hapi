#!/usr/bin/env python

""" capture loop test
    acq1001_caploop UUT1 [UUT2 ..]
    where UUT1 is the ip-address or host name of first uut
    example test client runs captures in a loop on one or more uuts

    pre-requisite: UUT's are configured and ready to make a transient
    capture 
    eg clk is running. soft trg enabled
    eg transient length set.

    loop continues "forever" until <CTRL-C>
"""

import sys
import acq400_hapi
import argparse
import os

SAVEDATA=os.getenv("SAVEDATA", None)

def run_loop(args):
    global SAVEDATA
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]             

    acq400_hapi.cleanup.init()

    if SAVEDATA:
        for u in uuts:
            u.save_data = SAVEDATA

    for uut in uuts:
        if hasattr(uut.s0, 'TIM_CTRL_LOCK'):
            print "LOCKDOWN {}".format(uut)
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
    parser.add_argument('uuts', nargs='+', help="uut pairs: m1,m2 [s1,s2 ...]")
    run_loop(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()




