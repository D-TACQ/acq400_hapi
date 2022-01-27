#!/usr/bin/env python

"""
generate a series of variable delays for GPG and plot
"""


import numpy as np
import matplotlib.pyplot as plt
import argparse
from lxml.html.builder import DD
from PIL.TiffImagePlugin import STRIPBYTECOUNTS
from lightdm_gtk_greeter_settings.OptionEntry import AccessibilityStatesEntry
   
def calc_lpd(args):
    data = []
    delay_ticks = [ x for x in range(args.d1, args.d2, args.ds)]
    print("delay_ticks: {}".format(delay_ticks))
    entry_count = 1+len(delay_ticks)*2
    counts = np.zeros((entry_count,), dtype=int)
    total = 0
    for ii, dd in enumerate(delay_ticks):
        total += dd
        counts[1+ii*2] = total        
        total += args.tpi - dd
        counts[1+ii*2+1] = total
        
    print(counts)
    states = [ 1 if ii%2==1 else 0 for ii in range(0, entry_count)]
    times = [ c * args.tns for c in counts]
    
    ctimes = [ x*args.tpi*args.tns/2 for x in range(0, len(states))]
    cstates = [ 1 if ii%2==1 else 0 for ii in range(0, len(states))]
    
    lpa = np.arange(0,5, step=(5/len(states)))
    
                            
    for ii in range(0, entry_count):
        print("{:5d},{}".format(counts[ii], states[ii]))
    
    nsp = 3
    
    
    ax0 = plt.subplot(nsp, 1, 1) 
    ax0.set_title("LP Delay Example")
    ax0.set_ylabel("{}".format("LPD"))   
    plt.step(times, states)
    plt.yticks(np.arange(0, 2, step=1))
    ax1 = plt.subplot(nsp, 1, 2, sharex=ax0)
    ax1.set_ylabel("{}".format("ADC CLK"))
    plt.step(ctimes, cstates)
    plt.yticks(np.arange(0, 2, step=1))
    
    ax2 = plt.subplot(nsp, 1, 3, sharex=ax0)
    ax2.set_ylabel("{}".format("AO3 LPA"))
    plt.step(ctimes, lpa)
    
    ax2.set_xlabel("Nano Seconds")
    plt.show()
    return len(states)//2    # return dwell in us

def calc_frame(args, dwell):
    ltime = args.line*dwell
    ltimes = [ t for t in range(0, ltime)]    
    ldac = [ x//dwell * 5 / args.line for x in ltimes ]
    
    ftimes = [ t for t in range(0, ltime*args.frame) ]
    fdac = [ x//ltime * 5 * args.frame for x in ftimes ]
    

    
    ax0 = plt.subplot(2, 1, 1)
    ax0.set_title("Raster Scan Example")
    ax0.set_ylabel("AO1 Frame V") 
    ax0.set_xlabel("Micro Seconds")      
    plt.step(ftimes, fdac)
    
    ax1 = plt.subplot(2, 1, 2)
    ax1.set_ylabel("AO2 Line V")   
    ax1.set_xlabel("Micro Seconds")
    plt.step(ltimes, ldac)
    plt.show()

def run_main():
    parser = argparse.ArgumentParser(description='multiplot')
    parser.add_argument('--d1', type=int, default=1, help="first delay (ticks)")
    parser.add_argument('--d2', type=int, default=25, help="last_delay+1 (ticks)")
    parser.add_argument('--ds', type=int, default=1, help="delay step (ticks)")
    parser.add_argument('--tpi', type=int, default=30, help="ticks per interval")
    parser.add_argument('--tns', type=float, default=16.6666, help="tick nsec")
    parser.add_argument('--frame', type=int, default=100, help="frame line count")
    parser.add_argument('--line', type=int, default=100, help="line pixel count")    
    
    
    args = parser.parse_args()
    dwell = calc_lpd(args)
    calc_frame(args, dwell)

if __name__ == '__main__':
    run_main()
