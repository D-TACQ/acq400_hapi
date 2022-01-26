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
   
def plot_data(args, data):
    plt.show()
    return None

def load_data(args):
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
                            
    for ii in range(0, entry_count):
        print("{:5d},{}".format(counts[ii], states[ii]))
        
    plt.step(times, states)
    plt.show()
    #counts = np
    return data

def run_main():
    parser = argparse.ArgumentParser(description='multiplot')
    parser.add_argument('--d1', type=int, default=1, help="first delay (ticks)")
    parser.add_argument('--d2', type=int, default=25, help="last_delay+1 (ticks)")
    parser.add_argument('--ds', type=int, default=1, help="delay step (ticks)")
    parser.add_argument('--tpi', type=int, default=30, help="ticks per interval")
    parser.add_argument('--tns', type=float, default=16.6666, help="tick nsec")    
    
    
    args = parser.parse_args()
    plot_data(args, load_data(args))

if __name__ == '__main__':
    run_main()
