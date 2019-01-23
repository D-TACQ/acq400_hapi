#!/usr/bin/env python

"""
A script used to test N UUTs syncd using sync_role. This script assumes this has
already been performed. A capture is performed and the
"""


import acq400_hapi
import time
import sys
import argparse


def run_test(args):

    ### Set up UUTs
    for num, uut in enumerate(args.uuts):
        args.uuts[num] = acq400_hapi.Acq400(uut)

    while True:

        ### Change trg to d4 on master
        args.uuts[0].s1.trg = "1,5,1"
        print "Setting trg to no trg"

        ### Arm uuts
        for uut in args.uuts:
            uut.s0.set_arm = 1
            acq400_hapi.shotcontrol.wait_for_state(uut, "ARM") # Pass hostname and required state
        print "Set arm"

        ### Change trigger back to external on master
        args.uuts[0].s1.trg = "1,0,1"
        print "Set trigger to ext"

        # Wait for UUTs to be IDLE again
        for uut in args.uuts:
            acq400_hapi.shotcontrol.wait_for_state(uut, "IDLE") # Pass hostname and required state

        # Check shot number across all UUTs
        shotnums = []
        for uut in args.uuts:
            shotnums.append(uut.s1.shot)

        if shotnums[1:] == shotnums[:-1]: # Check every element in list is identical
            print "Shot numbers agree. Success."
        else:
            print "Shot numbers do not agree. Fail."

        # Check all UUTs captured the correct number of samples
        samples = [] # store all "number of samples taken during shot" in list
        for uut in args.uuts:
            samples.append(uut.s0.TRANS_ACT_POST) # number of post shot samples

        if samples[1:] == samples[:-1]:
            print "# of samples recorded by each UUT are identical. Success."
        else:
            print "# of samples recorded by each UUT not identical. Fail."
            print "Ending test now"
            break

        print "Finished iteration"


def run_main():
    parser = argparse.ArgumentParser(description='synchronised trigger test')
    parser.add_argument('uuts', nargs='+', help='UUTs - master should be first')
    args = parser.parse_args()
    run_test(args)



if __name__ == '__main__':
    run_main()
