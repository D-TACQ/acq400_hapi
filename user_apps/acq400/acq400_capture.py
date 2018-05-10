#!/usr/bin/env python

""" capture test. assume transient has been pre-configured
    acq400_capture UUT1 [UUT2 ..]
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

def run_shot(args):
    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    acq400_hapi.cleanup.init()

    for uut in uuts:
        if args.transient != 'notouch':
            uut.s0.transient = args.transient.replace(',', ' ')
        if hasattr(uut.s0, 'TIM_CTRL_LOCK'):
            print "LOCKDOWN {}".format(uut)
            uut.s0.TIM_CTRL_LOCK = 1

    shot_controller = acq400_hapi.ShotController(uuts)

    try:
        shot_controller.run_shot(soft_trigger=args.soft_trigger)
        acq400_hapi.cleanup.sleep(1.0)            

    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")

# execution starts here

def run_main():
    parser = argparse.ArgumentParser(description='run capture, with optional transient configuration')
    parser.add_argument('--soft_trigger', type=int, default=True)
    parser.add_argument('--transient', default='notouch', help='transient control string use commas rather than spaces')
    parser.add_argument('uuts', nargs='+', help='uut1 [uut2..]')
    run_shot(parser.parse_args())

if __name__ == '__main__':
    run_main()




