#!/usr/bin/python -i

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
        def __init__(self, host, uut, lun=0, cycle=1):
            self.uut = uut
            self.host = host
            self.lun = lun
            self.cycle = cycle
            
        def load3(self, buf0=0, nchan=48):
            return load3("/data/{}".format(self.host), self.lun, self.uut, self.cycle, buf0, nchan)
        
loaders = [ LoadsHost(h, u, 0, 100) for (h, u) in (("Bolby", "acq2106_070"), ("Betso", "acq2106_071"),
                                       ("Ladna", "acq2106_072"), ("Vindo", "acq2106_073"))]
        
chx = [ l.load3() for l in loaders]




    