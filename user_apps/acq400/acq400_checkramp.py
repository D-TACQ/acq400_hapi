#!/usr/bin/env python

""" capture upload test
    acq1001_capplot UUT1 [UUT2 ..]
    where UUT1 is the ip-address or host name of first uut
    example test client runs captures in a loop on one or more uuts
    
    pre-requisite: UUT's are configured and ready to make a transient
    capture 
    eg clk is running. soft trg enabled
    eg transient length set.
    
    runs one capture, uploads the data and plots with matplotlib
    tested with 2 x 8 channels UUT's (ACQ1014)
    matplot will get very congested with more channels.
    this is really meant as a demonstration of capture, load to numpy,
    it's not really intended as a scope UI.
"""

import sys
import acq400_hapi
import numpy as np
import matplotlib.pyplot as plt
import os
import time

SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
TRACE_UPLOAD=int(os.getenv("TRACE_UPLOAD", "0"))
SAVEDATA=os.getenv("SAVEDATA", None)
PLOTDATA=int(os.getenv("PLOTDATA", "1"))
CAPTURE=int(os.getenv("CAPTURE", "1"))
PLOTTO=int(os.getenv("PLOTTO", "0"))

def run_main():
    global SOFT_TRIGGER,TRACE_UPLOAD, SAVEDATA, PLOTDATA, PLOTTO
    uuts = [  ]        
    if len(sys.argv) > 1:        
        for addr in sys.argv[1:]:            
            uuts.append(acq400_hapi.Acq400(addr))
    else:
        print("USAGE: acq1001_caploop UUT1 [UUT2 ..]")
        sys.exit(1)   


    acq400_hapi.cleanup.init()

    shot_controller = acq400_hapi.ShotController(uuts)

    try:  
        if CAPTURE:
            shot_controller.run_shot(soft_trigger=SOFT_TRIGGER)

        if SAVEDATA:
            for u in uuts:
                u.save_data = SAVEDATA
        if TRACE_UPLOAD:
            for u in uuts:
                u.trace = 1
                
        chx, ncol, nchan, nsam = shot_controller.read_channels((1,33))
      
# plot ex: 2 x 8 ncol=2 nchan=8
# U1 U2      FIG
# 11 21      1  2
# 12 22      3  4
# 13 23
# ...
# 18 28     15 16
        plt.ion()
        
        checks = []
        if PLOTDATA:
            for col in range(ncol):
                for chn in range(0,nchan):
                    fignum = 1 + col + chn*ncol
                    plt.subplot(nchan+1, ncol, fignum)                
                    plt.title("{} {}".format(uuts[col].uut, chn))
                    plt.plot(chx[col][chn])
                    
                checkramp = chx[col][nchan-1];
                ll = len(checkramp)              
                plt.subplot(nchan+1, ncol, fignum+3)
                checkramp = checkramp[1:ll-1] - checkramp[0:ll-2]
                plt.plot(checkramp)
                checks.append((np.amax(checkramp), np.amin(checkramp)))
            plt.draw()
            print("stats {}".format(checks))
            if PLOTTO > 0:
                while PLOTTO > 0:
                    time.sleep(1)
                    PLOTTO -= 1
            else:
                print("hit return to quit")
                sys.stdin.readline()
                
            plt.close()
            
    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")

# execution starts here

if __name__ == '__main__':
    run_main()




