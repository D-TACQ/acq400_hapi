#!/usr/bin/env python

import acq400_hapi
import time
import sys


def wait_for_state(uut, state, timeout=0):
    UUTS = [uut]
    time0 = 0
    if time0 == 0:
        time0 = time.time()
    for uut in UUTS:
        olds = ""
        finished = False
        dots = 0
        pollcat = 0

        while not finished:
            st = uut.s0.TRANS_ACT_STATE.split(' ')[1] #Real name TRANS_ACT:STATE
            finished = st == state
            news = "polling {}:{} {} waiting for {}".format(uut.uut, st, 'DONE' if finished else '', state)
            if news != olds:
                sys.stdout.write("\n{:06.2f}: {}".format(time.time() - time0, news))
                olds = news
            else:
                sys.stdout.write('.')
                dots += 1
                if dots >= 20:
                    dots = 0
                    olds = ""
            if not finished:
                if timeout and (time.time() - time0) > timeout:
                    sys.exit("\ntimeout waiting for {}".format(news))
                time.sleep(1)
            pollcat += 1
    print("")


### Set up UUTs
uut1 = acq400_hapi.Acq400(sys.argv[1]) # first arg
uut2 = acq400_hapi.Acq400(sys.argv[2]) # second arg

while True:

    ### Change trg to d4
    uut1.s1.trg = "1,5,1"
    print "Setting trg to no trg"

    ### Arm uuts
    uut2.s0.set_arm = 1
    wait_for_state(uut2, "ARM")
    uut1.s0.set_arm = 1
    wait_for_state(uut1, "ARM")
    print "Set arm"

    ### Change trigger back to external
    uut1.s1.trg = "1,0,1"
    print "Set trigger to ext"

    # Wait for UUTs to be IDLE again
    wait_for_state(uut1, "IDLE")
    wait_for_state(uut2, "IDLE")

    