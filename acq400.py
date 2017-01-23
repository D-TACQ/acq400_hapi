#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
acq400.py interface to one acq400 appliance instance
- enumerates all site services, available as uut.sX.knob
- simply property interface allows natural "script-like" usage
eg
uut1.s0.set_arm = 1

compared to 

set.site1 set_arm=1

- monitors transient status on uut, provides blocking events
- read_channels() - reads all data from channel data service.
Created on Sun Jan  8 12:36:38 2017

@author: pgm
"""

import threading
import re

import os
import signal
import sys
import netclient
import numpy

class AcqPorts:
    SITE0 = 4220
    TSTAT = 2235
    DATA0 = 53000

class SF:
    STATE = 0
    PRE = 1
    POST = 2
    ELAPSED = 3
    DEMUX = 5
    
class Channelclient(netclient.Netclient):
    def __init__(self, addr, ch):
        netclient.Netclient.__init__(self, addr, AcqPorts.DATA0+ch) 
        
    def read(self, ndata, data_size=2, maxbuf=4096):
        buffer = self.sock.recv(maxbuf)
        while len(buffer) < ndata*data_size:
            buffer += self.sock.recv(maxbuf)
            
        if data_size == 4:
            _dtype = numpy.dtype('i4')
        else:
            _dtype = numpy.dtype('i2')
            
        return numpy.frombuffer(buffer, dtype=_dtype, count=ndata)
        
        
class ExitCommand(Exception):
    pass


def signal_handler(signal, frame):
    raise ExitCommand()

class Statusmonitor:
    st_re = re.compile(r"([0-9]) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9])+" )

    def st_monitor(self):
        while self.quit_requested == False:
            st = self.logclient.poll()
            match = self.st_re.search(st)
            # status is a match. need to look at group(0). It's NOT a LIST!
            if match:
                statuss = match.groups()
                status1 = [int(x) for x in statuss]
                if self.trace:
                    print("uut:%s status:%s" % (self.uut, status1))
                if self.status != None:
#                    print("Status check %s %s" % (self.status0[0], status[0]))
                    if self.status[SF.STATE] != 0 and status1[SF.STATE] == 0:
                        print("%s STOPPED!" % (self.uut))
                        self.stopped.set()
#                print("status[0] is %d" % (status[0]))
                    if status1[SF.STATE] == 1:
                        print("%s ARMED!" % (self.uut))
                        self.armed.set()
                    if self.status[SF.STATE] == 0 and status1[SF.STATE] > 1:
                        print("ERROR: %s skipped ARM %d -> %d" % (self.uut, self.status[0], status1[0]))                        
                        self.quit_requested = True
                        os.kill(self.main_pid, signal.SIGINT)
                        sys.exit(1)                                            
                self.status = status1
                
    def wait_event(self, ev, descr):
 #       print("wait_%s 02 %d" % (descr, ev.is_set()))
        while ev.wait(0.1) == False:
            if self.quit_requested:
                print("QUIT REQUEST call exit %s" % (descr))
                sys.exit(1)
                
#        print("wait_%s 88 %d" % (descr, ev.is_set()))
        ev.clear()
#        print("wait_%s 99 %d" % (descr, ev.is_set()))        

    def wait_armed(self):
        self.wait_event(self.armed, "armed")

    def wait_stopped(self):
        self.wait_event(self.stopped, "stopped")


    def __init__(self, _uut, _status):
        self.quit_requested = False        
        self.trace = False
        self.uut = _uut
        self.main_pid = os.getpid()
        self.status = _status
        self.stopped = threading.Event()
        self.armed = threading.Event()
        self.logclient = netclient.Logclient(_uut, AcqPorts.TSTAT)
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
        s0 = self.svc["s0"] = netclient.Siteclient(self.uut, AcqPorts.SITE0)
        sl = s0.SITELIST.split(",")
        sl.pop(0)
        for sm in sl:
            site = int(sm.split("=").pop(0))
            self.svc["s%d" % site] = netclient.Siteclient(self.uut, AcqPorts.SITE0+site)
            self.__mod_count += 1

# init _status so that values are valid even if this Acq400 doesn't run a shot ..
        _status = [int(x) for x in s0.state.split(" ")]
        self.statmon = Statusmonitor(self.uut, _status)        


    def __getattr__(self, name):
        if self.svc.get(name) != None:
            return self.svc.get(name)
        else:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))
    
    def state(self):
        return self.statmon.status[SF.STATE]
    def post_samples(self):
        return self.statmon.status[SF.POST]
    def pre_samples(self):
        return self.statmon.status[SF.PRE]
    def elapsed_samples(self):
        return self.statmon.status[SF.ELAPSED]
    def demux_status(self):
        return self.statmon.status[SF.DEMUX]
    
    def read_chan(self, chan):
        cc = Channelclient(self.uut, chan)
        
        return cc.read(self.post_samples())
    
    def nchan(self):
        return int(self.s0.NCHAN)
    
    def read_channels(self):
        nchan = self.nchan()
        chx = []
        for ch in range(1,nchan+1):
            chx.append(self.read_chan(ch))
            
        return chx
            

def run_unit_test():
    SERVER_ADDRESS = '10.12.132.22'
    if len(sys.argv) > 1:
        SERVER_ADDRESS = sys.argv[1]

    print("create Acq400 %s" %(SERVER_ADDRESS))
    uut = Acq400(SERVER_ADDRESS)
    print("MODEL %s" %(uut.s0.MODEL))
    print("SITELIST %s" %(uut.s0.SITELIST))
    print("MODEL %s" %(uut.s1.MODEL))

    print("Module count %d" % (uut.mod_count))
    print("POST SAMPLES %d" % uut.post_samples())

    for sx in sorted(uut.svc):
        print("SITE:%s MODEL:%s" % (sx, uut.svc[sx].sr("MODEL")) )


if __name__ == '__main__':
    run_unit_test()

