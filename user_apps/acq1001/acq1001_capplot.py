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
import ast

SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
TRACE_UPLOAD=int(os.getenv("TRACE_UPLOAD", "0"))
SAVEDATA=os.getenv("SAVEDATA", None)
PLOTDATA=int(os.getenv("PLOTDATA", "-1"))
CAPTURE=int(os.getenv("CAPTURE", "1"))
CHANNELS=os.getenv("CHANNELS", None)
# CHANNELS: blank or () : ALL
# CHANNELS: 1 : channel 1
# CHANNELS: 1,5 : channels 1 and 5
# CHANNELS: (1,5),(1.6) : 1+5 uut1, 1+6 uut2

if CHANNELS == None:
    CHANNELS = ()
else:
    CHANNELS = ast.literal_eval(CHANNELS)

def run_main():
    global SOFT_TRIGGER,TRACE_UPLOAD, SAVEDATA, PLOTDATA, CHANNELS
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
                
        chx, ncol, nchan, nsam = shot_controller.read_channels(CHANNELS)
      
# plot ex: 2 x 8 ncol=2 nchan=8
# U1 U2      FIG
# 11 21      1  2
# 12 22      3  4
# 13 23
# ...
# 18 28     15 16
        if PLOTDATA:
            nplot = nchan if PLOTDATA < 0 else PLOTDATA
            for col in range(ncol):
                for chn in range(0, nplot):
                    fignum = 1 + col + chn*ncol
                    plt.subplot(nplot, ncol, fignum)                
                    plt.plot(chx[col][chn])

                
                        
            plt.show()
            
    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")

# execution starts here

if __name__ == '__main__':
    run_main()




