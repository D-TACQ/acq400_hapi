#!/usr/bin/env python3

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
        if args.data_type is None:
            data.append(np.load(fn))
        else:
            data.append(np.fromfile(fn, dtype=args.np_data_type))
        
    return data

def run_main(args):
    if args.data_type is None:
        print("plot .npy file")
    elif args.data_type == 16:
        args.np_data_type = np.int16
        args.WSIZE = 2
    elif args.data_type == 8:
        args.np_data_type = np.int8
        args.WSIZE = 1
    else:
        args.np_data_type = np.int32
        args.WSIZE = 4    
    
    plot_data(args, load_data(args))

def get_parser():
    parser = argparse.ArgumentParser(description='multiplot')
    parser.add_argument('--title', default="multiplot", help="Plot Title")
    parser.add_argument('--data_type', default=None, help="default: .npy file, else 16 or 32 for raw data")
    parser.add_argument('--maxlen', type=int, default=None, help="max length to plot")
    parser.add_argument('files', nargs='+', help='file names')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
