#!/usr/bin/python

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import subprocess


FMT = "%s/ACQ400DATA/%d/%s/%06d/%d.%02d"
#"/data/ACQ400DATA/%d/acq2106_070/000001/0.02"

def get_uut():
    p1 = subprocess.Popen(['get-ident'], stdout=subprocess.PIPE)
    return p1.communicate()[0].strip().split(' ')


uut = "acq2106_000"
(host, uut) = get_uut()

def load3(base="/data", lun=0, uut=uut, cycle=1, buf0=0, nchan=48):
    if buf0 % 3 != 0:
        print("ERROR, buf %d not modulo 3" % (buf0))
        exit(1)
    print("load3 {}".format(FMT % (base, lun, uut, cycle, lun, buf0)))
    b3 = tuple([ np.fromfile(FMT % (base, lun, uut, cycle, lun, buf0+x), np.int16) for x in range(3)] )
    raw = np.concatenate(b3)
    chx = np.reshape(raw, (raw.size/nchan, nchan))
    return (chx, lun, uut, cycle, nchan)

def plot16(l3, ic=0, nc=16):
    (chx, lun, uut, cycle, nchan) = l3
    for ch in range(ic,ic+nc):
        plt.plot(chx[:,ch])

    plt.title("uut: {} lun:{} ch {}..{}".format(uut, lun, ic+1, ic+nc+1))
    plt.xlabel("cycle {:06}".format(cycle))
    plt.show()


class LoadsHost:
    def __init__(self, host, uut):
        self.uut = uut
        self.host = host

    def load3(self, lun=0, cycle=1, buf0=0, nchan=48):
        return load3("data/{}".format(self.host), lun, self.uut, cycle, buf0, nchan)

loaders = [ LoadsHost(h, u) for (h, u) in (("Bolby", "acq2106_070"), ("Betso", "acq2106_071"),
                                           ("Ladna", "acq2106_072"), ("Vindo", "acq2106_073"))]

def get4(lun=0, cycle=1, buf0=0):
    return [ l.load3(lun, cycle, buf0) for l in loaders]

def bigplota(args):
    lenb = 0x400000
    len3 = 3*lenb
    ssize= 48*2
    sam3 = len3/ssize
    buffc = 99
    buffc3 = buffc/3

    M1 = 1000000
    SR = 2*M1

    pulsem = (0, 2, 4, 10, 20, 40, 100, 200)
    pp = 0
    for p in pulsem:
        samples = p*M1    
        buf3s = samples / sam3    
        residue = samples - buf3s * sam3            # residue, samples in triplet
        cycle = buf3s/buffc3                        # cycle from 0   
        cycb = 3*(buf3s - cycle*buffc3)              # buffer in cycle, first of 3
        
        buffers = buf3s * 3     
        cycle += 1                                  # counts from 1

        print("samples {} buffers {} residue {} cycle {} buffc {}".format(
            samples, buffers, residue, cycle, cycb))
        chx = get4(cycle=cycle, buf0=cycb)
        
        u0 = args.u1 - 1
        u1 = args.u2 if args.u2 >= args.u1 else args.ucount+u0
        c0 = args.c1 - 1
        c1 = args.c2 if args.c2 >= args.c1 else args.ccount+c0
      
	print("Hello {}".format(args.subplots))

        for u in range(u0, u1):
	    if args.subplots:
            	print("subplot {},{},{}".format(u1-u0,1,u1-u))
		ax = plt.subplot(u1-u0,1,u)
            for c in range(c0, c1):                
                plt.plot(chx[u][0][:,c], label='a{}.{}'.format(chx[u][2][8:], c+1))
            if args.subplots:
		ax.legend(loc='upper left', bbox_to_anchor=(1,1))

	if args.subplots == 0:
            plt.legend(loc='upper left', bbox_to_anchor=(1,1))
       
        plt.title("UUTS:{} at t {}s, pulse {} at sample {}".format(range(u0+1,u1+1), p*M1/SR, pp, p*M1))   
        plt.axvline(x=residue)
        plt.xlabel('cycle:{} buf:{}'.format(cycle, cycb))
        plt.show()          
        pp += 1

                
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="plots selected pulses")
    parser.add_argument("--u1", type=int, default=1, help="first uut (count from 1)")
    parser.add_argument("--u2", type=int, default=-1, help="last uut (count from 1), inclusive")
    parser.add_argument("--ucount", type=int, default=4, help="uut count unless overriden by --u2")
    parser.add_argument("--c1", type=int, default=1, help="first channel (count from 1)")
    parser.add_argument("--c2", type=int, default=-1, help="last channel (count from 1), inclusive")
    parser.add_argument("--ccount", type=int, default=4, help="channel count unless overridden by --c2")
    parser.add_argument("--subplots", type=int, default=0, help="set to 1 to plot with subplots per uut")
    bigplota(parser.parse_args())                 






