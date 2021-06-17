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
parser.add_argument('--nplot', default=10000, type=int)
parser.add_argument('--plot1', default=0, type=int, help="plot samples : 0:: do not plot")
parser.add_argument('--plot2', default=0, type=int, help="plot samples : 0:: do not plot")
parser.add_argument('--plotv', default=0, type=int)
parser.add_argument('--find_transitions', default=0, type=int, help="find transitions in data set")

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
args.volts = []

ODDS = (1,3,5,7,33,35,37,39)
EVEN = (0,2,4,6,32,34,36,38,64,66,68,70,96,98,100,102)
EVEN = (0,2,4,6,32,34,36,38)
#EVEN = (0,2,4,6,8,10,12,14)
#EVEN = (32,34,36,38,40,42,44,46)
for uut_name in args.uut_names:
    raw = np.fromfile("{}/{}/{:04d}.dat".format(args.root, uut_name, args.shot), np_type(args)).reshape((-1,args.nchan))
    print(raw.shape)
    diff = raw[0:len(raw)-shift] - raw[shift:,:]
    args.raw.append(raw)
    args.diff.append(diff)
    print("volts file {}".format("{}/{}/{:04d}.volts".format(args.root, uut_name, args.shot)))
    volts = np.fromfile("{}/{}/{:04d}.volts".format(args.root, uut_name, args.shot), np.dtype('f4')).reshape((-1,args.nchan))
    print(volts.shape)
    print("ch {} volts min {} max{}".format(0, min(volts[:,0]), max(volts[:,0])))
    args.volts.append(volts)

if args.plotv > 0:
    fig, axes = plt.subplots(3)
    vnom = np.multiply(args.raw[0][:args.plotv,EVEN], 1.25/32768)
    ENAMES = [i+1 for i in EVEN]
    axes[0].plot(vnom)
    axes[0].set_title('{} {} Nominal Volts'.format(args.uut_names[0], ENAMES))
    axes[0].legend()
    vcal = args.volts[0][:args.plotv,EVEN]
    axes[1].plot(vcal)
    axes[1].set_title('{} {} Calibrated Volts'.format(args.uut_names[0], ENAMES))
    axes[2].plot(np.subtract(vcal, vnom))
    axes[2].set_title('{} {} Calibrated - Nominal Volts'.format(args.uut_names[0], ENAMES))
    plt.show()
    
if args.plot1:
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


PLOT2_CHANS=(0, 2, 32, 34)
PLOT2_CHANS_ALL= [i for i in range(0, 64, 2)]

if args.plot2 == 1:
    print("Plot2: show volts on box 1, 2 sites 1, 2")
    for u in range(0, len(args.uut_names)):
        for c in PLOT2_CHANS_ALL:
            plt.plot(args.volts[u][:args.nplot,c], label="{}.CH{:03d}".format(args.uut_names[u], c+1))
    plt.title("Plot2.1 shot {}".format(args.shot))
    plt.legend()
    plt.show()

if args.plot2 == 2:
    print("Plot2.2: show volts all odds all boxes, 8 per subplot")
    nu = len(args.uut_names)
    nsubs = nu*32//8
    
    fig, axes = plt.subplots(nsubs)
    fig.canvas.set_window_title("Plot2.2: all odd channels {}, 8 per subplot".format(' '.join(args.uut_names)))
    for sub in range(0, nsubs):
        u = 0 if sub < nsubs//nu else 1
        c1 = (sub%4)*16
        for ch in range(c1, c1+16, 2):
            axes[sub].plot(args.volts[u][:args.nplot,ch], label="CH{:03d}".format(ch+1))
        axes[sub].set_title("uut: {} shot {}".format(args.uut_names[u], args.shot))
        axes[sub].set_xlabel("samples")
        axes[sub].set_ylabel("V")
        axes[sub].legend()
    plt.show()    


def min_sep(edges):
    sep = edges[1:len(edges)] - edges[0:len(edges)-1]
    return min(sep)

def max_sep(edges):
    sep = edges[1:len(edges)] - edges[0:len(edges)-1]
    return max(sep)


if args.find_transitions:
    transitions = []
    for ix in range(0, len(args.uut_names)):
        for ch in range (0, 128, 2):
            tx = np.where(args.diff[ix][:,ch] > 100)[0]
            tx = find_max(tx, args.diff[ix][:,ch])
            transitions.append(tx)
            tl = len(tx)
            if tl > 0:
                print("{} ch:{:03d} : first:{} n:{} sep:min:{},max:{} {},{}".\
                    format(args.uut_names[ix], ch+1, tx[0], len(tx), min_sep(tx), max_sep(tx), tx[0:3], tx[tl-3:tl]))
            else:
                print("{} ch:{:03d} : NO TRANSITIONS".format(args.uut_names[ix], ch+1))






    





