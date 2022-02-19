#!/usr/bin/env python

"""
plot multiple single channel data sets stored as .npy files
"""


import numpy as np
import matplotlib.pyplot as plt
import argparse
   
def plot_data(args, data):
    nsp = len(data)
    plen = min([len(d) for d in data])
    if args.maxlen and args.maxlen < plen:
        plen = args.maxlen
        
    tt = range(0, plen)
          
    for sp in range(0,nsp):        
        if sp == 0:
            ax0 = plt.subplot(nsp,1,sp+1)
            ax0.set_title(args.title)
            ax = ax0
        else:
            ax = plt.subplot(nsp,1,sp+1, sharex=ax0)
        lastplot = sp == nsp-1
            
        ax.set_ylabel("{}".format(sp))                  
        plt.plot(tt, data[sp][:plen])
        plt.tick_params('x', labelbottom=lastplot)
 

    ax.set_xlabel("Samples")
    plt.show()
    return None

def load_data(args):
    data = []
    for fn in args.files:
        data.append(np.load(fn))
    return data

def run_main():
    parser = argparse.ArgumentParser(description='multiplot')
    parser.add_argument('--title', default="multiplot", help="Plot Title")
    parser.add_argument('--maxlen', type=int, default=None, help="max length to plot")
    parser.add_argument('files', nargs='+', help='file names')
    
    args = parser.parse_args()
    plot_data(args, load_data(args))

if __name__ == '__main__':
    run_main()
