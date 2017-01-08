#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 12:36:38 2017

@author: pgm
"""

import sys
import netclient


class Acq400:
    svc = {}
    __mod_count = 0
    @property 
    def mod_count(self):
        return self.__mod_count
        
    def __init__(self, _uut):
        self.uut = _uut
        s0 = self.svc["s0"] = netclient.Siteclient(self.uut, 4220)
        sl = s0.SITELIST.split(",")
        sl.pop(0)
        for sm in sl:
            site = int(sm.split("=").pop(0))
            self.svc["s%d" % site] = netclient.Siteclient(self.uut, 4220+site)
            self.__mod_count += 1
        

    def __getattr__(self, name):
        if self.svc.get(name) != None:
                return self.svc.get(name)
        else:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError(msg.format(type(self).__name__, name))


if __name__ == '__main__':
   SERVER_ADDRESS = '10.12.132.18'
   if len(sys.argv) > 1:
        SERVER_ADDRESS = sys.argv[1]

   print("create Acq400 %s" %(SERVER_ADDRESS))
   uut = Acq400(SERVER_ADDRESS)
   print("MODEL %s" %(uut.s0.MODEL))
   print("SITELIST %s" %(uut.s0.SITELIST))
   print("MODEL %s" %(uut.s1.MODEL))
   
   print("Module count %d" % (uut.mod_count))
   
   for sx in sorted(uut.svc):
       print("SITE:%s MODEL:%s" % (sx, uut.svc[sx].sr("MODEL")) )
       


    
