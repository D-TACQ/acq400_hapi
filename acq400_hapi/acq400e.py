#!/usr/bin/env python3

"""epics based acq400 equivalent 

Usage:

from acq400_hapi.acq400e import acq400e

uut = acq400e('acq2106_000')

uut.s0.NCHAN

"""

import epics
import time
import socket
from enum import Enum

LINE_UP = '\033[1A'
ERASE_LINE = '\033[2K'

class States(Enum):
    IDLE = 0
    ARM = 1
    RUNPRE = 2
    RUNPOST = 3
    POPROCESS = 4
    CLEANUP = 5

class Ports(Enum):
    STREAM = 4210

class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

class acq400e:
    """ acq400 class using epics """
    def __init__(self, uut):
        self.uut = uut
        self.sites = DotDict({
            'acq': [],
            'ao': [],
            'dio': [],
            'agg': [],
        })

        self.pvs = {}
        self.stop_flag = False
        self.datafile = f"{self.uut}.dat"

        self.get_sites()
        self.int_statemon()

    def get_sites(self):
        self.s0 = self.Site(self.uut, 0)
        sitelist = self.caget(f"{self.uut}:SITELIST")
        for site in sitelist.split(','):
            if len(site.split('=')) != 2: continue
            site, _ = site.split('=')
            id = f"s{site}"
            setattr(self, id, self.Site(self.uut, site))

            if self[site].model.lower().startswith('acq'):
                self.sites.acq.append(site)
            if self[site].model.lower().startswith('ao'):
                self.sites.ao.append(site)
            if self[site].model.lower().startswith('dio'):
                self.sites.dio.append(site)

        self.sites.agg = self.s0.AGGREGATOR_SITES.split(',')
    
    def __getitem__(self, site):
        return getattr(self, f"s{site}")
    
    def int_statemon(self):
        self.cstate = None
        cstate_callback = lambda value, **kwargs: setattr(self, 'cstate', value)
        cstate_pv = "{uut}:MODE:CONTINUOUS:STATE"
        self.monitor(cstate_pv, cstate_callback)

        self.tstate = None
        tstate_callback = lambda value, **kwargs: setattr(self, 'tstate', value)
        tstate_pv = "{uut}:MODE:TRANS_ACT:STATE"
        self.monitor(tstate_pv, tstate_callback)

    @staticmethod
    def caget(pvname):
        response = epics.caget(pvname, connection_timeout=2)
        if response == None: raise AttributeError(f"unable to access pv {pvname}")
        return response

    @staticmethod
    def caput(pvname, pvvalue):
        response = epics.caput(pvname, pvvalue, wait=True, connection_timeout=2)
        if response == None: raise AttributeError(f"unable to access pv {pvname}")
        return response

    def monitor(self, pv, callback=None):
        """Monitor a pv and run a callback function when it updates"""
        def pv_callback(pvname, value, **kwargs):
            print("pv_callback")
            self.pvs[pvname].value = value
        
        callback = callback if callback else pv_callback
        pvname = pv.format(uut=self.uut)
        self.pvs[pvname] = DotDict()
        self.pvs[pvname].pv = epics.PV(pvname, callback=callback, auto_monitor=True)
        self.pvs[pvname].value = None

    def clearpv(self, pv):
        """Stop monitoring a pv"""
        pvname = pv.format(uut=self.uut)
        self.pvs[pvname].pv.clear_callbacks()
        del(self.pvs[pvname])

    def readpv(self, pv):
        """Read the value of a pv"""
        pvname = pv.format(uut=self.uut)
        return self.pvs[pvname].value
    
    def stream_to_disk(self, ssb=None, maxbytes=None, maxtime=None, update=True):

        ssb = ssb if ssb else int(self.s0.SSB)
        bufferlen = ssb * 1024

        buffer = bytearray(bufferlen)
        byteview = memoryview(buffer).cast('B')
        print("Starting Stream")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.uut, Ports.STREAM.value))
            with open(self.datafile, 'wb') as fp:
                index = 0
                tbytes = 0
                t0 = 0
                while True:
                    nbytes = sock.recv_into(byteview[index:])

                    if nbytes == 0: 
                        print('Error: uut has stoppped')
                        break

                    index += nbytes
                    tbytes += nbytes

                    if t0 == 0: t0 = time.time()

                    if index >= bufferlen:
                        if update:
                            tt = time.time() - t0
                            print(f"Streaming {int(tt)}s {(tbytes >> 20) / tt:.5f} MB/s > {self.datafile}")

                        fp.write(buffer[:index])
                        index = 0

                        if maxtime and time.time() - t0 > maxtime:
                            print('Stream reached max time')
                            break

                        if maxbytes and tbytes >= maxbytes:
                            print('Stream reached max bytes')
                            break

                        if self.stop_flag:
                            print("Stream received stop signal")
                            break

                        if update: print(LINE_UP + ERASE_LINE , end="")

                fp.flush()
            sock.shutdown(socket.SHUT_RDWR)
        print(f"{tbytes:,} bytes {tbytes // ssb:,} samples total")

    def stop_stream(self):
        self.stop_flag = True

    class Site:
        def __init__(self, uut, site):
            site = int(site)
            object.__setattr__(self, "uut", uut)
            object.__setattr__(self, "site", site)
            if site > 0:
                object.__setattr__(self, "nchan", self.NCHAN)
                object.__setattr__(self, "data_len", 4 if int(self.data32) else 2)
                object.__setattr__(self, "model", self.MODEL)
            
        def __getattr__(self, pvname):
            pvname = self.clean(pvname)
            return acq400e.caget(f"{self.uut}:{self.site}:{pvname}")
        
        def __setattr__(self, pvname, value):
            pvname = self.clean(pvname)
            value = ','.join(map(str, value)) if type(value) is list else value
            return acq400e.caput(f"{self.uut}:{self.site}:{pvname}", value)
        
        def clean(self, pvname):
            """Corrects pvnames
               Converts _ to :
               Converts __ to _
            """
            pvname = pvname.replace("__", '$')
            pvname = pvname.replace("_", ':')
            pvname = pvname.replace("$", '_')
            return pvname