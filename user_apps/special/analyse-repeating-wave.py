import numpy as np
import argparse
import sys
import scipy.signal

import matplotlib.pyplot as plt

def np_type(args):
   return np.int16

parser = argparse.ArgumentParser(description='make_awg_data')
parser.add_argument('--shot', default=1, type=int)
parser.add_argument('--chan', default=32, type=int)
parser.add_argument('--plot', default=100000, type=int, help="plot samples : 0:: do not plot")

parser.add_argument('uut_names', nargs='+', help="uut names")

def find_max(x, f):
    m = []
#    print("find_max {} shape {}".format(len(x), np.shape(x)))
    for i in range(1, len(x)-1):
        mx = 1 if f[x[i]] > f[x[i-1]] and f[x[i]] >= f[x[i+1]] else 0
#        print("consider {} {} {} : {}".format(x[i-1], x[i], x[i+1], mx))
        if mx:
#            print("find_max at {}".format(i))
            m.append(x[i])
    return np.array(m)


args = parser.parse_args()
args.nchan = 128
args.root="."

shift=1
args.raw = []
args.diff = []

ODDS = (1,3,5,7,33,35,37,39)
EVEN = (0,2,4,6,32,34,36,38,64,66,68,70,96,98,100,102)
for uut_name in args.uut_names:
    raw = np.fromfile("{}/{}/{:04d}.dat".format(args.root, uut_name, args.shot), np_type(args)).reshape((-1,args.nchan))
    diff = raw[0:len(raw)-shift] - raw[shift:,:]
    args.raw.append(raw)
    args.diff.append(diff)

if args.plot:
    fig, axes = plt.subplots(8)
    for xx in range(0, 2):
        axes[xx*4+0].plot(args.raw[xx][:args.plot,ODDS])
        axes[xx*4+0].set_title('{} Raw[odds]'.format(args.uut_names[xx]))
        axes[xx*4+0].legend()
        axes[xx*4+1].plot(args.diff[xx][:args.plot,ODDS])
        axes[xx*4+1].set_title('{} Diff[odds]'.format(args.uut_names[xx]))
        axes[xx*4+2].plot(args.raw[xx][:args.plot,EVEN])
        axes[xx*4+2].set_title('{} Raw[evens]'.format(args.uut_names[xx]))
        axes[xx*4+3].plot(args.diff[xx][:args.plot,EVEN])
        axes[xx*4+3].set_title('{} Diff[evens]'.format(args.uut_names[xx]))
    plt.show()
    for ch in EVEN:
        plt.plot(args.raw[0][:args.plot,ch], label="CH{:03d}".format(ch), marker = '' if ch < 32 or ch >= 64 else 'o')
    plt.legend()
    plt.show()

def min_sep(edges):
    sep = edges[1:len(edges)] - edges[0:len(edges)-1]
    return min(sep)

def max_sep(edges):
    sep = edges[1:len(edges)] - edges[0:len(edges)-1]
    return max(sep)


transitions = []
#for ch in range (0, args.nchan):
for ch in range (0, 128, 8):
#    for ix in range(0, 2):
    for ix in range(0, 1):
        tx = np.where(args.diff[ix][:,ch] > 100)[0]
        tx = find_max(tx, args.diff[ix][:,ch])
        transitions.append(tx)
        tl = len(tx)
        print("{} ch:{:03d} : first:{} n:{} sep:min:{},max:{} {},{}".format(args.uut_names[ix], ch, tx[0], len(tx), min_sep(tx), max_sep(tx), tx[0:3], tx[tl-3:tl]))




    





