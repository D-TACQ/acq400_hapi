#!/usr/bin/env python

"""
generate a series of variable delays for GPG and plot
"""


import numpy as np
import matplotlib.pyplot as plt
import argparse

def make_raw_binary(args, counts, states):    
    b_out = np.zeros(len(counts), dtype=np.int32)
    ii_out = 0
    for ii, st in enumerate(states):
        print("mrb {} {} {}".format(ii, counts[ii], st))

        until_count = counts[ii]-1
        if until_count < 4:
            until_count = 4
        
        if ii == 0:
            st |= 2                              # sync output for scope trigger
        if ii+1 == len(states) and args.kludge_flyback:
            until_count += 1                    # gpg flyback drops one clock, claw it back
        b_out[ii_out] = until_count << 8 | st
        ii_out += 1
    
    b_out = b_out[:ii_out]
    with open("gpg_x{}.raw".format(args.rawscale), "wb") as fd:
        b_out.tofile(fd)


def calc_lpd(args):
    data = []
    delay_ticks = [ x for x in range(args.d1, args.d2, args.ds)]
    print("delay_ticks: {}".format(delay_ticks))
    entry_count = len(delay_ticks)*2
    counts = np.zeros((entry_count,), dtype=int)
    total = 0
    for ii, dd in enumerate(delay_ticks):
        total += dd
        counts[ii*2] = total        
        total += args.tpi - dd
        counts[ii*2+1] = total
        
    print("counts {}\n{}".format(len(counts), counts))
    
    states = [ 1 if ii%2==0 else 0 for ii in range(0, entry_count)]
    times = [ c * args.tns for c in counts]
    
    ctimes = [ x*args.tpi*args.tns/2 for x in range(0, len(states))]
    cstates = [ 1 if ii%2==1 else 0 for ii in range(0, len(states))]
    
    lpa = np.arange(0,5, step=(5/len(states)))
    
    make_raw_binary(args, counts, states)                
    
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
    parser.add_argument('--d1', type=int, default=4, help="first delay (ticks)")
    parser.add_argument('--d2', type=int, default=16+4+1, help="last_delay+1 (ticks)")
    parser.add_argument('--ds', type=int, default=1, help="delay step (ticks)")
    parser.add_argument('--tpi', type=int, default=30, help="ticks per interval")
    parser.add_argument('--tns', type=float, default=16.6666, help="tick nsec")
    parser.add_argument('--frame', type=int, default=100, help="frame line count")
    parser.add_argument('--line', type=int, default=100, help="line pixel count")
    parser.add_argument('--kludge_flyback', type=int, default=0, help="fixup for GPG logic")
    parser.add_argument('--rawscale', type=int, default=1, help="scale raw gpg output for slower output easier to see DO NOT USE!")   
    
    
    args = parser.parse_args()
    dwell = calc_lpd(args)
    calc_frame(args, dwell)

if __name__ == '__main__':
    run_main()
