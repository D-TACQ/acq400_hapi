
import numpy as np
import os
from acq400_hapi.awg_data import AwgDefaults

class ZeroOffset:   
    def __init__(self, uut, nchan, nsam, target=0, run_forever=False, gain = 0.1, passvalue = 1, aochan = 0, ao0 = 0):
        print("ZeroOffset")
        self.uut = uut
        self.nchan = nchan
        self.nsam = nsam
        self.target = float(target)
        self.run_forever = run_forever
        if aochan == 0:
            aochan = nchan
        self.aw = np.zeros((nsam,aochan))
        for ch in range(0, aochan):
            self.aw[:,ch] = ch
        self.aw.astype('int16').tofile("awg.dat")
        self.current = np.zeros(nchan)
        self.finished = 0
        self.in_bounds = False
        self.KFB = gain
        self.passvalue = float(passvalue/gain)
        self.identity_pattern = bool(int(os.getenv("IDENTITY_PATTERN", 0)))
        self.verbose = int(os.getenv("VERBOSE", 0))
        self.ao0 = ao0
        self.user_quit = False
        self.defs = AwgDefaults(uut.uut)
        # offsets compensate channel geometry when AWG disabled
        self.apply_geometry = bool(int(os.getenv("AO_CORRECT_GEOMETRY", 0)))
        self.geometry = [ 
            -2*3.3, 0, 0, -2*3.3, 0, 0, 0, 6*3.3, 
                0, 0, 0, 0, 0, -3*3.3, 0, 0,
                -2*3.3, 0, 0, -2*3.3, 0, 0, 0, 6*3.3, 
                0, 0, 0, 0, 0, -3*3.3, 0, 0
        ]

        try:
            print("self.identity_pattern {}".format(self.identity_pattern))
            if not self.identity_pattern:
                self.current = self.defs.read_defaults()
                for ch in range(0, self.nchan):            
                    self.aw[:,self.ao0+ch] = self.current[ch]

        except IOError:
            print("no defaults")

    def vprint(self, str):
        if self.verbose > 0:
            print(str)

    def feedback(self, fb_data):
        actual = np.mean(fb_data[50:,:], axis=0)
        error = actual - self.target
        errmax = max(abs(error))
        if  errmax < self.passvalue:
            print("maximum error {} is within bounds {}, save it".format(errmax, self.passvalue))
            self.defs.store_defaults(self.current)
            self.in_bounds = True
        else:
            print("maximum error {}".format(errmax))
  
        self.current = np.mean(self.aw, axis=0)[self.ao0:self.ao0+self.nchan]
        self.newset = self.current + (self.target - actual) * self.KFB
        self.newset = np.clip(self.newset, -32768, 32767)

        if np.max(self.newset) >= 32767 or np.min(self.newset) <= 32768:
            print("Hit rails good idea to quit")
            passcount=0
	    railcount=0
            for e in np.nditer(error):
		if abs(e) < self.passvalue:
                    passcount += 1
                elif abs(e) >= 32767:
                    railcount +=1
            if passcount+railcount > len(error)/2:
                self.in_bounds = True

        if self.verbose or self.in_bounds:
            np.set_printoptions(linewidth=200, precision=3)
            print("target  {}".format(self.target))
            print("current {}".format(self.current))
            print("actual  {}".format(actual))
            print("error   {}".format(error))
            print("errma   {}".format(errmax))
            print("gain    {}".format(self.KFB))
            print("step    {}".format((self.target - actual) * self.KFB))
            print("newset  {}".format(self.newset))        
        if not self.identity_pattern:
            for ch in range(0, self.nchan):            
                self.aw[:,self.ao0+ch] = self.newset[ch]

        self.aw.astype('int16').tofile("awg.dat")


        

    def load(self, autorearm = False):
        self.vprint("load 01")
        yy = self
        while not self.finished:
            self.vprint("load 10")
            if self.finished and self.apply_geometry:
                print("apply_geometry")
                for ch in range(0, self.nchan):
                    self.aw[:,ch] += self.geometry[ch]
                yy = None
            self.uut.load_awg(self.aw.astype(np.int16), autorearm = autorearm)           
            print("loaded array ", self.aw.shape)
            if self.in_bounds:
                # plot this one, drop out next time
                print("Target achieved, quit any time")
                self.finished = True
            self.vprint("load 66")
            yield yy

        self.vprint("load 99")



