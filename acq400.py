#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 12:36:38 2017

@author: pgm
"""

import threading
import re

import sys
import netclient

TLC_PORT = 2235

class Statusmonitor:
    st_re = re.compile(r"([0-9]) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9])+" )

    def st_monitor(self):
        while True:
            st = self.logclient.poll()
            match = self.st_re.search(st)
            # status is a match. need to look at group(0). It's NOT a LIST!
            if match:
                statuss = match.groups()
                status = [int(x) for x in statuss]
                print("uut:%s status:%s" % (self.uut, status))
                if self.status0 != None:
                    print("Status check %s %s" % (self.status0[0], status[0]))
                    if self.status0[0] != 0 and status[0] == 0:
                        print("%s STOPPED!" % (self.uut))
                        self.stopped.set()
                print("status[0] is %d" % (status[0]))
                if status[0] == 1:
                    print("%s ARMED!" % (self.uut))
                    self.armed.set()
                    
                self.status0 = status

# todo maybe more elegant to "curry" these two or somesuch pythonic cleverness?
    def wait_armed(self):
        print("wait_armed02 %d" % (self.armed.is_set()))
        self.armed.wait()
        print("wait_armed88 %d" % (self.armed.is_set()))
        self.armed.clear()
        print("wait_armed99 %d" % (self.armed.is_set()))

    def wait_stopped(self):
        self.stopped.wait()
        self.stopped.clear()


    def __init__(self, _uut):
        self.uut = _uut
        self.status0 = None
        self.stopped = threading.Event()
        self.armed = threading.Event()
        self.logclient = netclient.Logclient(_uut, TLC_PORT)
        self.st_thread = threading.Thread(target=self.st_monitor)
        self.st_thread.setDaemon(True)
        self.st_thread.start()      
        # need some way to stop the thread.


class Acq400:
    @property 
    def mod_count(self):
        return self.__mod_count

    def __init__(self, _uut):
        self.uut = _uut
        self.svc = {}
        self.__mod_count = 0    
        s0 = self.svc["s0"] = netclient.Siteclient(self.uut, 4220)
        sl = s0.SITELIST.split(",")
        sl.pop(0)
        for sm in sl:
            site = int(sm.split("=").pop(0))
            self.svc["s%d" % site] = netclient.Siteclient(self.uut, 4220+site)
            self.__mod_count += 1

        self.statmon = Statusmonitor(self.uut)        


    def __getattr__(self, name):
        if self.svc.get(name) != None:
            return self.svc.get(name)
        else:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))


if __name__ == '__main__':
    SERVER_ADDRESS = '10.12.132.22'
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




