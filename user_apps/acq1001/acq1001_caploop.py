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


def run_main():
    uuts = [  ]        
    if len(sys.argv) > 1:       
        for addr in sys.argv[1:]:            
            uuts.append(acq400_hapi.Acq400(addr))
    else:
        print("USAGE: acq1001_caploop UUT1 [UUT2 ..]")
        sys.exit(1)        

    acq400_hapi.cleanup.init()

    for uut in uuts:
        if hasattr(uut.s0, 'TIM_CTRL_LOCK'):
            print "LOCKDOWN {}".format(uut)
            uut.s0.TIM_CTRL_LOCK = 1

    shot_controller = acq400_hapi.ShotController(uuts)

    try:
        while True:
            shot_controller.run_shot(soft_trigger=True)
            acq400_hapi.cleanup.sleep(1.0)            
            
    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")

# execution starts here

if __name__ == '__main__':
    run_main()




