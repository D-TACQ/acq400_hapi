#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 12:36:38 2017

@author: pgm
"""

import netclient


class Acq400:
    svc = {}
    def __init__(self, _uut):
        self.uut = _uut
        self.svc["s0"] = netclient.Siteclient(self.uut, 4220)
        

    def __getattr__(self, name):
        if self.svc.get(name) != None:
                return self.svc.get(name)
        else:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError(msg.format(type(self).__name__, name))


if __name__ == '__main__':
   SERVER_ADDRESS = '10.12.132.18'

   uut = Acq400(SERVER_ADDRESS)
   print("MODEL %s" %(uut.s0.MODEL))
   print("SITELIST %s" %(uut.s0.SITELIST))


    
