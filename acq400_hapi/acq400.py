#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
acq400.py interface to one acq400 appliance instance

- enumerates all site services, available as uut.sX.knob
- simple property interface allows natural "script-like" usage
 - eg::

       uut1.s0.set_arm = 1

 - equivalent to running this on a logged in shell session on the UUT::

       set.site1 set_arm=1

 - monitors transient status on uut, provides blocking events
 - read_channels() - reads all data from channel data service.
  Created on Sun Jan  8 12:36:38 2017

  @author: pgm
"""

import threading
import re

import os
import errno
import signal
import sys

if __name__ == '__main__':
    import netclient
else:
    from . import netclient

import numpy as np
import socket
import timeit
import time

class AcqPorts:
    """server port constants"""
    TSTAT = 2235
    STREAM = 4210
    SITE0 = 4220
    SEGSW = 4250
    SEGSR = 4251
    DPGSTL = 4521
    GPGSTL= 4541
    GPGDUMP = 4543

    WRPG = 4606

    DIO482_PG_STL = 45001  
    DIO482_PG_DUMP = DIO482_PG_STL+2
    
    BOLO8_CAL = 45072
    DATA0 = 53000
    DATAT = 53333
    MULTI_EVENT_TMP = 53555
    MULTI_EVENT_DISK = 53556
    DATA_SPY = 53667
    LIVETOP = 53998
    ONESHOT = 53999
    AWG_ONCE = 54201
    AWG_AUTOREARM = 54202
    AWG_CONTINUOUS = 54205
    AWG_STREAM = 54207
    MGTDRAM = 53993
    MGTDRAM_PULL_DATA = 53991

class AcqSites:
    # site service at AcqPorts.SITE0+ AcqSites.SITEi
    SITE0 = 0
    SITE1 = 1
    SITE2 = 2
    SITE3 = 3
    SITE4 = 4
    SITE5 = 5
    SITE6 = 6
    SITE_CA = 13
    SITE_CB = 12
    SITE_CC = 11
    SITE_DSP = 14

class SF:
    """state constants"""
    STATE = 0
    PRE = 1
    POST = 2
    ELAPSED = 3
    DEMUX = 5

class STATE:
    """transient states"""
    IDLE = 0
    ARM = 1
    RUNPRE = 2
    RUNPOST = 3
    POPROCESS = 4
    CLEANUP = 5
    @staticmethod
    def str(st):
        if st==STATE.IDLE:
            return "IDLE"
        if st==STATE.ARM:
            return "ARM"
        if st==STATE.RUNPRE:
            return "RUNPRE"
        if st==STATE.RUNPOST:
            return "RUNPOST"
        if st==STATE.POPROCESS:
            return "POPROCESS"
        if st==STATE.CLEANUP:
            return "CLEANUP"
        return "UNDEF"

class Signals:
    EXT_TRG_DX = 'd0'
    INT_TRG_DX = 'd1'
    MB_CLK_DX = 'd1'

class StreamClient(netclient.Netclient):
    """handles live streaming data"""
    def __init__(self, addr):
        print("worktodo")

class RawClient(netclient.Netclient):
    """ handles raw data from any service port
    """
    def __init__(self, addr, port):
        netclient.Netclient.__init__(self, addr, port)

    def read(self, nelems, data_size=2):
        """read ndata from channel data server, return as np array.
        Args:
            nelems number of data elements, each data_size*ncols
            nelems <=0 :: read until the end

            data_size : 2|4 short or int

            ncols : optional, to create a 2D array
            ncols*data_size=0? just read nelems bytes
        """
        _dtype = np.dtype('i4' if data_size == 4 else 'i2')   # hmm, what if unsigned?

        buf = bytearray(nelems)
        try:
            view = memoryview(buf).cast('B')
        except:
            # python 2.7 hack
            view = memoryview(buf)
        pos = 0
        while len(view):
            nrx = self.sock.recv_into(view)
            if nrx == 0:
                break               # end of file
            view = view[nrx:]
            pos += nrx

        if pos > 0 and pos < nelems:
            print("WARNING: early termination at {}/{}".format(pos, nelems))
        return np.frombuffer(buf[:pos], _dtype)

    def get_blocks(self, nelems, data_size=2):
        block = np.array([1])
        while len(block) > 0:
            block = self.read(nelems, data_size=data_size)
            if len(block) > 0:
                yield block


class MgtDramPullClient(RawClient):
    def __init__(self, addr):
        RawClient.__init__(self, addr, AcqPorts.MGTDRAM_PULL_DATA)



class ChannelClient(netclient.Netclient):
    """handles post shot data for one channel.

    Args:
        addr (str) : ip address or dns name

        ch (int) : channel number 1..N

    """
    def __init__(self, addr, ch):
        netclient.Netclient.__init__(self, addr, AcqPorts.DATA0+ch)

# on Linux, recv returns on ~mtu
# on Windows, it may buffer up, and it's very slow unless we use a larger buffer
    def read(self, ndata, data_size=2, maxbuf=0x400000):
        """read ndata from channel data server, return as np array.
        Args:
            ndata (int): number of elements

            data_size : 2|4 short or int

            maxbuf=4096 : max bytes to read per packet

        Returns:
            np: data array

        * TODO buffer +=

         this is probably horribly inefficient probably better::

          retbuf = np.array(dtype, ndata)
          retbuf[cursor].

        """
        _dtypes = { 1 : 'i1', 2: 'i2', 4: 'i4' }
        _dtype = np.dtype(_dtypes[data_size])
        total_buffer = buffer = self.sock.recv(maxbuf)

        if int(ndata) == 0 or int(ndata) == -1:
            while True:
                buffer = self.sock.recv(maxbuf)
                if not buffer:
                    return np.frombuffer(total_buffer, dtype=_dtype, count=-1)
                total_buffer += buffer

        while len(buffer) < ndata*data_size:
            buffer += self.sock.recv(maxbuf)

        return np.frombuffer(buffer, dtype=_dtype, count=ndata)


class ExitCommand(Exception):
    pass


def signal_handler(signal, frame):
    raise ExitCommand()

class Statusmonitor:
    """ monitors the status channel

    Efficient event-driven monitoring in a separate thread
    """
    st_re = re.compile(r"([0-9]) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9])+" )

    def __repr__(self):
        return repr(self.logclient)
    def st_monitor(self):
        while self.quit_requested == False:
            try:
                st = self.logclient.poll()
            except OSError as err:
                if self.quit_reqested:
                    return
                else:
                    raise err
                
            match = self.st_re.search(st)
            # status is a match. need to look at group(0). It's NOT a LIST!
            if match:
                statuss = match.groups()
                status1 = [int(x) for x in statuss]
                if self.trace > 1:
                    print("%s <%s" % (repr(self), status1))
                if self.status != None:
#                    print("Status check %s %s" % (self.status0[0], status[0]))
                    if self.status[SF.STATE] != 0 and status1[SF.STATE] == 0:
                        if self.trace:
                            print("%s STOPPED!" % (self.uut))
                        self.stopped.set()
                        self.armed.clear()
#                print("status[0] is %d" % (status[0]))
                    if status1[SF.STATE] == 1:
                        if self.trace:
                            print("%s ARMED!" % (self.uut))
                        self.armed.set()
                        self.stopped.clear()
                    if self.status[SF.STATE] == 0 and status1[SF.STATE] > 1:
                        if self.trace:
                            print("ERROR: %s skipped ARM %d -> %d" % (self.uut, self.status[0], status1[0]))
                        self.quit_requested = True
                        os.kill(self.main_pid, signal.SIGINT)
                        sys.exit(1)
                self.status = status1
            elif self.trace > 1:
                print("%s <%s>" % (repr(self), st))

    def get_state(self):
        return self.status[SF.STATE]
    
    def get_pre(self):
        return self.status[SF.PRE]

    def get_post(self):
        return self.status[SF.POST]
    
    def get_total(self):
        return self.get_pre() + self.get_post()
    

    def wait_event(self, ev, descr):
    #       print("wait_%s 02 %d" % (descr, ev.is_set()))
        while ev.wait(0.1) == False and not self.break_requested:
            if self.quit_requested:
                print("QUIT REQUEST call exit %s" % (descr))
                sys.exit(1)

#        print("wait_%s 88 %d" % (descr, ev.is_set()))
        ev.clear()
#        print("wait_%s 99 %d" % (descr, ev.is_set()))

    def wait_armed(self):
        """
        blocks until uut is ARMED
        """
        self.wait_event(self.armed, "armed")

    def wait_stopped(self):
        """
        blocks until uut is STOPPED
        """
        self.wait_event(self.stopped, "stopped")

    trace = int(os.getenv("STATUSMONITOR_TRACE", "0"))
    

    def __init__(self, _uut, _status):
        self.break_requested = False
        self.quit_requested = False
        self.trace = Statusmonitor.trace
        self.uut = _uut
        self.main_pid = os.getpid()
        self.status = _status
        self.stopped = threading.Event()
        self.armed = threading.Event()
        self.logclient = netclient.Logclient(_uut, AcqPorts.TSTAT)
        self.st_thread = threading.Thread(target=self.st_monitor)
        self.st_thread.setDaemon(True)
        self.st_thread.start()


class NullFilter:
    def __call__ (self, st):
        print(st)

null_filter = NullFilter()

class ProcessMonitor:
    st_rex = ( re.compile(r"^END" ), re.compile(r"^real"))

    def st_monitor(self):
        while self.quit_requested == False:
            st = self.logclient.poll()
            self.output_filter(st)
            for re in self.st_rex:
            	if re.search(st):
                    self.quit_requested = True
                    break

    def __init__(self, _uut, _monport,  _filter, set_arm):
        self.quit_requested = False
        self.output_filter = _filter
        self.logclient = netclient.Logclient(_uut.uut, _monport)
        self.logclient.termex = re.compile("(\n)")
        self.st_thread = threading.Thread(target=self.st_monitor)
        self.st_thread.setDaemon(True)
        self.st_thread.start()
        if set_arm:
            _uut.s0.BLT_SET_ARM = '1'

class Acq400:
    """
    host-side proxy for Acq400 uut.

    discovers and maintains all site servers
    maintains a monitor thread on the monitor port
    handles multiple channel post shot upload

    Args:
        _uut (str) : ip-address or dns name

        monitor=True (bool) : set false to stub monitor,
          useful for tracing on a second connection to an active system.
    """

    def init_site_client(self, site):
        svc = netclient.Siteclient(self.uut, AcqPorts.SITE0+site)
        self.svc["s%d" % site] = svc
        self.modules[site] = svc

        if self.awg_site == 0 and svc.module_name.startswith("ao"):
            self.awg_site = site
        self.mod_count += 1
        
    
    @classmethod
    def create_uuts(cls, uut_names):
        """ create_uuts():  factory .. create them in parallel

        *** Experimental Do Not Use ***

        """
        uuts = []
        uut_threads = {}
        for uname in uut_names:
            uut_threads[uname] = \
                    threading.Thread(\
                        target=lambda u, l: l.append(cls(u)), \
                        args=(uname, uuts))
        for uname in uut_names:
            uut_threads[uname].start()
        for t in uut_threads:
            uut_threads[t].join(10.0)

        return uuts

    uuts_methods = {}        # for cloning by new
    uuts = {}                # for re-use by factory
    
    def __init__(self, _uut, monitor=True, s0_client=None):
        try:
            self.__dict__ = Acq400.uuts_methods[_uut]
            return
        except KeyError:
            pass
   
        self.verbose = int(os.getenv("ACQ400_VERBOSE", "0"))    
        self.NL = re.compile(r"(\n)")
        self.uut = _uut
        self.trace = 0
        self.save_data = None
        self.svc = {}
        self.modules = {}
        self.mod_count = 0
        # channel index from 1,..
        self.cal_eslo = [0, ]
        self.cal_eoff = [0, ]
        self.mb_clk_min = 4000000

        s0 = self.svc["s0"] = s0_client if s0_client else netclient.Siteclient(self.uut, AcqPorts.SITE0)
        sl = s0.SITELIST.split(",")
        sl.pop(0)
        self.awg_site = 0
        site_enumerators = {}
        for sm in sl:
            site_enumerators[sm] = \
                    threading.Thread(target=self.init_site_client,\
                        args=(int(sm.split("=").pop(0)),)\
                    )
        for sm in sl:
            site_enumerators[sm].start()

        for sm in sl:
#            print("join {}".format(site_enumerators[sm]))
            site_enumerators[sm].join(10.0)
            
        self.sites = [int(s.split('=')[0]) for s in sl]

# init _status so that values are valid even if this Acq400 doesn't run a shot ..
        _status = [int(x) for x in s0.state.split(" ")]
        if monitor:
            self.statmon = Statusmonitor(self.uut, _status)
        Acq400.uuts_methods[_uut] = self.__dict__   # store the dict for reuse by __init__
        Acq400.uuts[_uut] = self                    # store the object for reuse by factory()

    def close(self):
        self.statmon.quit_reqested = True
        self.statmon.logclient.close()
        for k, s in self.svc.items():
            s.close()
        try:
            del Acq400.uuts[self.uut]
            del Acq400.uuts_methods[self.uut]
        except KeyError:
            print("ERROR {} instance not in cache".format(self.uut))

    def __del__(self):
        print("__del__ {}".format(self.uut))

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
    def samples(self):
        return self.pre_samples() + self.post_samples()

    def get_aggregator_sites(self):
        return self.s0.aggregator.split(' ')[1].split('=')[1].split(',')

    def fetch_all_calibration(self):
#        print("Fetching calibration data")
        for m in (self.modules[int(c)] for c in self.get_aggregator_sites()):
            self.cal_eslo.extend(m.AI_CAL_ESLO.split(' ')[3:])
            self.cal_eoff.extend(m.AI_CAL_EOFF.split(' ')[3:])

    def scale_raw(self, raw, volts=False):
        for (sx, m) in list(self.modules.items()):
            if m.MODEL.startswith("ACQ43"):
                rshift = 8
            elif m.data32 == '1':
                # volts calibration is normalised to 24b
                if m.adc_18b == '1':
                    rshift = 14 - (8 if volts else 0)
                else:
                    rshift = 16 - (8 if volts else 0)
            else:
                rshift = 0
            break
        return np.right_shift(raw, rshift)

    def chan2volts(self, chan, raw):
        """ chan2volts(self, chan, raw) returns calibrated volts for channel

            Args:

               chan: 1..nchan

               raw:  raw bits to convert.

        """
        if len(self.cal_eslo) == 1:
            self.fetch_all_calibration()

        eslo = float(self.cal_eslo[chan])
        eoff = float(self.cal_eoff[chan])
        if self.verbose > 1 or (self.verbose and chan < 4):
            print("chan {} v = {}*{} + {}".format(chan, raw[0], eslo, eoff))
        
        return np.add(np.multiply(raw, eslo), eoff)


    def read_chan(self, chan, nsam = 0, data_size = None):
        if chan != 0 and nsam == 0:
            nsam = self.pre_samples()+self.post_samples()
        if data_size == None:
            data_size = 4 if self.s0.data32 == '1' else 2

        cc = ChannelClient(self.uut, chan)
        ccraw = cc.read(nsam, data_size=data_size)

        if self.save_data:
            try:
                os.makedirs(self.save_data)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

            with open("%s/%s_CH%02d" % (self.save_data, self.uut, chan), 'wb') as fid:
                ccraw.tofile(fid, '')

        return ccraw

    def read_decims(self, nsam = 0):
        if nsam == 0:
            nsam = self.pre_samples()+self.post_samples()
        cc = ChannelClient(self.uut, AcqPorts.DATAT-AcqPorts.DATA0)
        ccraw = cc.read(nsam, data_size=1)

        if self.save_data:
            try:
                os.makedirs(self.save_data)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

            with open("%s/%s_DEC" % (self.save_data, self.uut, chan), 'wb') as fid:
                ccraw.tofile(fid, '')

        return ccraw


    def nchan(self):
        try:
            return self._nchan
        except:        
            self._nchan = int(self.s0.NCHAN)        
            return self._nchan


    def data_size(self):
	    return 4 if self.s0.data32 == '1' else 2
    
    def uut_demux_enabled(self):
        ts = self.s0.transient
        rc = bool(int(self.s0.transient.split("DEMUX=",1)[1][0]))
#        print ("uut_demux_enabled(): transient {} decoded DEMUX={} rc={}".format(ts, ts.split("DEMUX=",1)[1][0], rc))
        return rc

    def read_channels(self, channels=(), nsam=0, localdemux=False):
        """read all channels post shot data.

        Returns:
            chx (list) of np arrays.
            
        uut_demux_enabled() == False: UUT did NOT demux the data, data order [sample][channel] 
        uut_demux_enabled() == True:  UUT did demux the data, data order [channel][sample]
        
        DEMUX is a synonym for uut_demux_enabled()..
        
        channels=(0) : return all (bulk) data, likely in raw[sample][channel] format.
        channels=(0) localdemux=True: return all (bulk) in demux[channel][sample] format. 
        
        channels=N or channels=(N,N1,N2 ..)   # N >= 1 && N <= NCHAN
        
        There are 4 cases:
        channels=(1,2...nchan) and (remote) DEMUX=1: SIMPLE, pull each channel at a time from the UUT.        
        channels=(0) and DEMUX=0 : SIMPLE: return the raw data.
        
        channels=(1,2..) and DEMUX=1 : demux locally.
        
        channels=(0) and DEMUX=0 and localdemux : demux locally, return bulk data [channels][samnples]
        """


        if channels == ():
            channels = list(range(1, self.nchan()+1))
        elif type(channels) == int:
            channels = (channels,)
            
        bulk_channels = channels == (0,)

        chx = []
        data_size = 4 if self.s0.data32 == '1' else 2
        if self.uut_demux_enabled():
           localdemux = False
        else:
            if not bulk_channels:
                localdemux = True 
        
        if not localdemux:
#            print("read_channels() NOT localdemux")
            # likely: either pull channelized demux data or pull a full set of raw data.
            for ch in channels:
                if self.trace:
                    print("%s CH%02d start.." % (self.uut, ch))
                    start = timeit.default_timer()

                chx.append(self.read_chan(ch, nsam, data_size=data_size))

                if self.trace:
                    tt = timeit.default_timer() - start
                    print("%s CH%02d complete.. %.3f s %.2f MB/s" %
                        (self.uut, ch, tt, len(chx[-1])*2/1000000/tt))
        else:
            # only do local demux if client wants it and the data needs it..
            data = np.array(self.read_chan(0, nsam, data_size=data_size))
            data = data.reshape((-1, self.nchan()))
            if bulk_channels:
 #               print("read_channels() local demux, bulk data")
                channels = np.arange(0, self.nchan())
            else:
 #               print("read_channels() local demux, selected channels")
                channels = np.array(channels)-1
                
            data = data[:,channels].transpose()
            chx = [ item for item in data ]

        return chx

    def read_transient_timebase(self, nsamples, pre=0):
        try:
            fs = freq(self.s1.ACQ480_OSR)
        except:
            fs = freq(self.s0.SIG_CLK_S1_FREQ)
        if fs > 1e6:
            isi = 1 / np.round(fs / 1e6, 2) * 1e-6  # interval in seconds
        else:
            isi = 1 / np.round(fs / 1e3, 2) * 1e-3  # interval in seconds
        return np.linspace(-pre*isi, (nsamples-pre)*isi, nsamples)
    # DEPRECATED
    def load_segments(self, segs):
        with netclient.Netclient(self.uut, AcqPorts.SEGSW) as nc:
            for seg in segs:
                nc.sock.send((seg+"\n").encode())
    # DEPRECATED
    def show_segments(self):
        with netclient.Netclient(self.uut, AcqPorts.SEGSR) as nc:
            while True:
                buf = nc.sock.recv(1024)
                if buf:
                    print(buf)
                else:
                    break

    def clear_counters(self):
        for s in self.svc:
            self.svc[s].sr('*RESET=1')

    def set_sync_routing_master(self, clk_dx="d1", trg_dx="d0"):
        self.s0.SIG_SYNC_OUT_CLK = "CLK"
        self.s0.SIG_SYNC_OUT_CLK_DX = clk_dx
        self.s0.SIG_SYNC_OUT_TRG = "TRG"
        self.s0.SIG_SYNC_OUT_TRG_DX = trg_dx

    def set_sync_routing_slave(self):
        self.set_sync_routing_master()
        self.s0.SIG_SRC_CLK_1 = "HDMI"
        self.s0.SIG_SRC_TRG_0 = "HDMI"

    def set_sync_routing(self, role):
        # deprecated
        # set sync mode on HDMI daisychain
        # valid roles: master or slave
        if role == "master":
            self.set_sync_routing_master()
        elif role == "slave":
            self.set_sync_routing_slave()
        else:
            raise ValueError("undefined role {}".format(role))

    def set_mb_clk(self, hz=4000000, src="zclk", fin=1000000):
        hz = int(hz)
        if src == "zclk":
            self.s0.SIG_ZCLK_SRC = "INT33M"
            self.s0.SYS_CLK_FPMUX = "ZCLK"
            self.s0.SIG_CLK_MB_FIN = 33333000
        elif src == "xclk":
            self.s0.SYS_CLK_FPMUX = "XCLK"
            self.s0.SIG_CLK_MB_FIN = 32768000
        else:
            self.s0.SYS_CLK_FPMUX = "FPCLK"
            self.s0.SIG_CLK_MB_FIN = fin

        if hz >= self.mb_clk_min:
            self.s0.SIG_CLK_MB_SET = hz
            self.s1.CLKDIV = '1'
        else:
            for clkdiv in range(1,2000):
                if hz*clkdiv >= self.mb_clk_min:
                    self.s0.SIG_CLK_MB_SET = hz*clkdiv
                    self.s1.CLKDIV = clkdiv
                    return
            raise ValueError("frequency out of range {}".format(hz))

    def load_stl(self, stl, port, trace = False, wait_eof = True, wait_eol = True):
        termex = re.compile("\n")
        with netclient.Netclient(self.uut, port) as nc:
            lines = stl.split("\n")
            for ll in lines:
                if trace:
                    print("> {}".format(ll))
                if len(ll) < 2:
                    if trace:
                        print("skip blank")
                    continue
                if ll.startswith('#'):
                    if trace:
                        print("skip comment")
                    continue
                nc.sock.send((ll+"\n").encode())
                if wait_eol:
                    rx = nc.sock.recv(4096)
                    if trace:
                        print("< {}".format(rx))
            nc.sock.send("EOF\n".encode())
            nc.sock.shutdown(socket.SHUT_WR)
            while wait_eof:
                rx = nc.sock.recv(4096)
                if trace:
                    print("< {}".format(rx))
                if (str(rx).find("EOF")) != -1:
                    break
                wait_end = wait_eof



    def load_gpg(self, stl, trace = False):
            self.load_stl(stl, AcqPorts.GPGSTL, trace)

        
    def load_dpg(self, stl, trace = False):
        self.load_stl(stl, AcqPorts.DPGSTL, trace, wait_eol=False)

    def load_wrpg(self, stl, trace = False):
        self.load_stl(stl, AcqPorts.WRPG, trace)
        
    def load_dio482pg(self, site, stl, trace = False):
        self.load_stl(stl, AcqPorts.DIO482_PG_STL+int(site)*10, trace)
        
    def set_DO(self, site, dox, value = 'P'):
        self.svc["s{}".format(site)].set_knob("DO_{}".format(dox), value)        

    class AwgBusyError(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)

    def load_awg(self, data, autorearm=False, continuous=False, repeats=1):
        if self.awg_site > 0:
            if self.modules[self.awg_site].task_active == '1':
                raise self.AwgBusyError("awg busy")
        port = AcqPorts.AWG_CONTINUOUS if continuous else AcqPorts.AWG_AUTOREARM if autorearm else AcqPorts.AWG_ONCE

        with netclient.Netclient(self.uut, port) as nc:
            while repeats:
                nc.sock.send(data)
                repeats -= 1
            nc.sock.shutdown(socket.SHUT_WR)
            while True:
                rx = nc.sock.recv(128)
                if self.trace and rx:
                    print("<{}".format(rx))
                if not rx or rx.startswith(b"DONE"):
                    break
            nc.sock.close()
    
    def run_service(self, port, eof="EOF", prompt='>'):
        txt = ""
        with netclient.Netclient(self.uut, port) as nc:
            while True:
                rx = nc.receive_message(self.NL, 256)
                txt += rx
                txt += "\n"
                print("{}{}".format(prompt, rx))
                if rx.startswith(eof):
                    break
            nc.sock.shutdown(socket.SHUT_RDWR)
            nc.sock.close()

        return txt

    def run_oneshot(self):
        with netclient.Netclient(self.uut, AcqPorts.ONESHOT) as nc:
            while True:
                rx = nc.receive_message(self.NL, 256)
                print("{}> {}".format(self.s0.HN, rx))
                if rx.startswith("SHOT_COMPLETE"):
                    break
            nc.sock.shutdown(socket.SHUT_RDWR)
            nc.sock.close()

    def run_livetop(self):
        with netclient.Netclient(self.uut, AcqPorts.LIVETOP) as nc:
            print(nc.receive_message(self.NL, 256))
            nc.sock.shutdown(socket.SHUT_RDWR)
            nc.sock.close()


    def disable_trigger(self):
        #master.s0.SIG_SRC_TRG_0 = 'NONE'
        #master.s0.SIG_SRC_TRG_1 = 'NONE'
        self.s0.SIG_SRC_TRG_0 = 'NONE'
        self.s0.SIG_SRC_TRG_1 = 'NONE'

    def enable_trigger(self, trg_0='EXT', trg_1='STRIG'):
        if trg_0 is not None:
            self.s0.SIG_SRC_TRG_0 = trg_0
        if trg_1 is not None:
            self.s0.SIG_SRC_TRG_1 = trg_1

    def configure_post(self, role, trigger=[1,1,1], post=100000):
        """
        Configure UUT for a regular transient capture. Default: internal soft
        trigger starts the capture.

        "Role" is a mandatory argument. For master systems, role should be the
        string "master", if the system is a slave then role should be the string
        "slave"

        Default post samples: 100k.
        """
        print(trigger)
        self.s0.transient = "PRE=0 POST={} SOFT_TRIGGER={}".format(post, trigger[1])

        self.s1.TRG = 1
        if role == "slave" or trigger[1] == 0:
            self.s1.TRG_DX = 0
        else:
            self.s1.TRG_DX = 1
        self.s1.TRG_SENSE = trigger[2]

        self.s1.EVENT0 = 0
        self.s1.EVENT0_DX = 0
        self.s1.EVENT0_SENSE = 0

        self.s1.RGM = 0
        self.s1.RGM_DX = 0
        self.s1.RGM_SENSE = 0

        self.s1.RGM = 0 # Make sure RGM mode is turned off.
        self.s0.SIG_EVENT_SRC_0 = 0

        return None


    def configure_pre_post(self, role, trigger=[1,1,1], event=[1,1,1], pre=50000, post=100000):
        """
        Configure UUT for pre/post mode. Default: soft trigger starts the
        data flow and trigger the event on a hard external trigger.

        "Role" is a mandatory argument. For master systems, role should be the
        string "master", if the system is a slave then role should be the string
        "slave"

        Default pre trigger samples: 50k.
        Default post trigger samples: 100k.
        """
        if pre > post:
            print("PRE samples cannot be greater than POST samples. Config not set.")
            return None
        trg = 1 if trigger[1] == 1 else 0
        self.s0.transient = "PRE={} POST={} SOFT_TRIGGER={}".format(pre, post, trg)

        self.s1.TRG = trigger[0]
        if role == "slave" or trigger[1] == 0:
            self.s1.TRG_DX = 0
        else:
            self.s1.TRG_DX = 1
        self.s1.TRG_SENSE = trigger[2]

        self.s1.EVENT0 = event[0]
        self.s1.EVENT0_DX = event[1]
        self.s1.EVENT0_SENSE = event[2]

        self.s1.RGM = 0
        self.s1.RGM_DX = 0
        self.s1.RGM_SENSE = 0

        self.s1.RGM = 0 # Make sure RGM mode is turned off.
        self.s0.SIG_EVENT_SRC_0 = 0
        return None


    def configure_rtm(self, role, trigger=[1,1,1], event=[1,1,1], post=50000, rtm_translen=5000, gpg=0):
        """
        Configure UUT for rtm mode. Default: external trigger starts the capture
        and takes 5000 samples, each subsequent trigger gives us another 5000
        samples.

        "Role" is a mandatory argument. For master systems, role should be the
        string "master", if the system is a slave then role should be the string
        "slave"

        Default rtm_translen: 5k samples.
        Default post: 50k samples

        GPG can be used in RTM mode as the Event. If you are using the GPG
        then this function can put the GPG output onto the event bus (to use as
        an Event for RTM).
        """
        self.s0.transient = "PRE=0 POST={}".format(post)
        self.s1.rtm_translen = rtm_translen
        self.s1.TRG = 1
        if role == "slave" or trigger[1] == 0:
            self.s1.TRG_DX = 0
        else:
            self.s1.TRG_DX = 1
        self.s1.TRG_SENSE = trigger[2]

        self.s1.EVENT0 = event[0]
        self.s1.EVENT0_DX = event[1]
        self.s1.EVENT0_SENSE = event[2]

        self.s1.RGM = 3
        self.s1.RGM_DX = 0
        self.s1.RGM_SENSE = 1

        self.s0.SIG_EVENT_SRC_0 = 1 if gpg == 1 else 0

        return None

    def configure_transient(self, pre=0, post=100000,
        sig_DX='d0', auto_soft_trigger=0, demux=1, edge='rising'):
        """
        Configure uut for transient capture.
        sig_DX is the signal line responsible for TRIGGER or EVENT depending on mode;
        function makes appropriate selection.
        Function is aware of sync_role and sets sig_DX accordingly
        """
        sync_role = self.s0.sync_role
        if sync_role == 'role not set' and sync_role == 'slave':
            sig_DX = 'd0'

        sigdef = "1,{},{}".format(sig_DX[1], 1 if edge == 'rising' else 0)

        if pre > 0:
            self.s1.event0 = sigdef
            self.s1.trg = '1,1,1'
        else:
            self.s1.event0 = '0,0,0'
            self.s1.trg = sigdef

        self.s0.transient = "PRE={} POST={} SOFT_TRIGGER={} DEMUX={}".\
            format(pre, post, auto_soft_trigger, demux)





    def configure_rgm(self, role, trigger=[1,0,1], event=[1,1,1], post="100000", gpg=0):
        """
        Configure UUT for RGM mode. Default: external trigger starts the capture
        and the system takes samples every clock whenever the trigger is high.

        "Role" is a mandatory argument. For master systems, role should be the
        string "master", if the system is a slave then role should be the string
        "slave"

        Default post: 100k samples.

        GPG can be used in RGM mode as the Event. If you are using the GPG then
        this function can put the GPG output onto the event bus (to use as an
        Event for RGM).

        """
        self.s0.transient = "PRE=0 POST={}".format(post)
        self.s1.TRG = 1
        if role == "slave" or trigger[1] == 0:
            self.s1.TRG_DX = 0
        else:
            self.s1.TRG_DX = 1
        self.s1.TRG_SENSE = trigger[2]

        self.s1.EVENT0 = 0#event[0]
        self.s1.EVENT0_DX = 0#event[1]
        self.s1.EVENT0_SENSE = 0

        self.s1.RGM = 2
        self.s1.RGM_DX = 0
        self.s1.RGM_SENSE = 1

        self.s0.SIG_EVENT_SRC_0 = 1 if gpg == 1 else 0

        return None


    def get_demux_state(self):
        """
        Returns the current state of demux. Beware: if demux is set after the
        shot then this function will return the new state. There is no way to
        determine what the state was during the previous shot.
        """
        transient = self.s0.transient
        demux_state = transient.split("DEMUX=",1)[1][0]
        return int(demux_state)


    def pull_plot(self, channels=(), demux=-1):
        """
        Pulls data from 53000 or 5300X depending on the status of demux.
        This function takes a tuple of integers and will return the
        corresponding data from each 5300X port (if demux is on) and will return
        the corresponding data filtered from 53000 if demux is off.

        The user can also override the detected demux state if they want to: 1
        is demux on and 0 is demux off. Default is -1 and means autodetect.

        This function returns an array of the specified channels and plots the
        data.
        """
        data = []
        if demux == -1:
            demux = self.get_demux_state()
        if demux == 1:
            data = self.read_channels(channels)
        elif demux == 0:
            mux_data = self.read_muxed_data()
            print("mux data = ", mux_data)
            nchan = self.nchan()
            if channels == ():
                channels = list(range(1,nchan+1))
            for ch in channels:
                print("Channel - ", ch)
                data.append(mux_data[ch-1::nchan])

        import matplotlib.pyplot as plt
        for channel in data:
            plt.plot(channel)
        plt.grid(True)
        plt.show()
        return data


    def read_muxed_data(self):
        """
        A function that returns data from port 53000. Only use if demux is
        turned off. If demux is turned on then this function will not return the
        expected muxed data. To check if demux is enabled use the
        get_demux_state() function.
        """
        data = self.read_channels((0), -1)
        return data[0]


    def pull_data(self):
        """
        A function to pull data based on whatever demux is set to. Should be
        entirely automated. The function will check what channels are AI
        channels and pull the data from those channels.
        """

        demux_state = self.get_demux_state()
        channels = list(range(1, self.get_ai_channels()+1))
        nchan = channels[-1]

        if demux_state == 1:
            data = self.read_channels(channels, -1)
        elif demux_state == 0:
            data = []
            mux_data = self.read_muxed_data()
            for ch in channels:
                data.append(mux_data[ch-1::nchan])

        return data


    def get_ai_channels(self):
        """
        Returns all of the AI channels. This is a more robust way to get the
        total number of AI channels, as sometimes nchan can be set to include
        the scratch pad.
        """
        ai_channels = 0
        site_types = self.get_site_types()
        for ai_site in site_types["AISITES"]:
            ai_site = "s{}".format(ai_site)
            ai_channels += int(getattr(getattr(self, ai_site), "NCHAN"))

        return ai_channels

    def get_site_types(self):
        """
        Returns a dictionary with keys AISITES, AOSITES, and DIOSITES with the
        corresponding values as lists of the channels which are AI, AO, and DIO.
        """
        AISITES = []
        AOSITES = []
        DIOSITES = []

        for site in [1,2,3,4,5,6]:
            try:
                module_name = eval('self.s{}.module_name'.format(site))
                if module_name.startswith('acq'):
                    AISITES.append(site)
                elif module_name.startswith('ao'):
                    AOSITES.append(site)
                elif module_name.startswith('dio'):
                    DIOSITES.append(site)
            except Exception:
                continue

        site_types = { "AISITES": AISITES, "AOSITES": AOSITES, "DIOSITES": DIOSITES }
        return site_types

    def get_es_indices(self, file_path="default", nchan="default", human_readable=0, return_hex_string=0):
        """
        Returns the location of event samples.

        get_es_indices will pull data from a system by default (it will also
        read in a raw datafile) and reads through the data in order to find the
        location of the event samples. The system will also return the raw
        event sample data straight from the system.

        If human_readable is set to 1 then the function will return the hex
        interpretations of the event sample data. The indices will remain
        unchanged.

        If return_hex_string is set to 1 (provided human_readable has ALSO been
        set) then the function will return one single string containing all of
        the event samples.

        Data returned by the function looks like:
        [  [Event sample indices], [Event sample data]  ]
        """
        # a function that return the location of event samples.
        # returns:
        # [ [event sample indices], [ [event sample 1], ...[event sample N] ] ]
        indices = []
        event_samples = []
        nchan = self.nchan() if nchan == "default" else nchan

        if file_path == "default":
            data = self.read_muxed_data()
            data = np.array(data)
            if data.dtype == np.int16:
                # convert shorts back to raw bytes and then to longs.
                data = np.frombuffer(data.tobytes(), dtype=np.uint32)
        else:
            data = np.fromfile(file_path, dtype=np.uint32)

        if int(self.s0.data32) == 0:
            nchan = nchan / 2 # "effective" nchan has halved if data is shorts.
        nchan = int(nchan)
        for index, sample in enumerate(data[0::nchan]):
            # if sample == np.int32(0xaa55f154): # aa55
            if sample == np.uint32(0xaa55f154): # aa55
                indices.append(index)
                event_samples.append(data[index*nchan:index*nchan + nchan])

        if human_readable == 1:
            # Change decimal to hex.
            ii = 0
            while ii < len(event_samples):
                if type(event_samples[ii]) == np.ndarray:
                    event_samples[ii] = event_samples[ii].tolist()
                for indice, channel in enumerate(event_samples[ii]):
                    event_samples[ii][indice] = '0x{0:08X}'.format(channel)
                ll = int(len(event_samples[ii])/int(len(self.get_aggregator_sites())))
                # print(event_samples[ii])
                event_samples[ii] = [event_samples[ii][i:i + ll] for i in range(0, len(event_samples[ii]), ll)]
                ii += 1

            if return_hex_string == 1:
                # Make a single string containing the hex values.
                es_string = ""
                for num, sample in enumerate(event_samples):
                    for i in range(len(sample[0])):
                        for x in event_samples[num]:
                            es_string = es_string + str(x[i]) + " "
                        es_string = es_string + "\n"
                    es_string = es_string + "\n"
                event_samples = es_string

        return [indices, event_samples]

    def stream(self, recvlen=4096*32, port=AcqPorts.STREAM, data_size=2):
        dtype = np.dtype('i4' if data_size == 4 else 'i2')   # hmm, what if unsigned?
        nc = netclient.Netclient(self.uut, AcqPorts.STREAM)

        buf = bytearray(recvlen*data_size)
        while True:       
            view = memoryview(buf).cast('B')        
            pos = 0
            
            while len(view):
                nrx = nc.sock.recv_into(view)
                if nrx == 0:                    
                    yield np.frombuffer(buf[:pos], dtype)
                    pos = 0
                else:
                    view = view[nrx:]
                    pos += nrx
            yield np.frombuffer(buf[:pos], dtype)


    @staticmethod
    def freq(sig):
        return float(sig.split(" ")[1])

    @staticmethod
    def intpv(pv):
        return int(pv.split(" ")[1])
    @staticmethod
    def pv(pv):
        return pv.split(" ")[1]


class Acq2106(Acq400):
    """ Acq2106 specialization of Acq400

    Defines features specific to ACQ2106
    """

    def __init__(self, _uut, monitor=True, s0_client=None, has_dsp=False, has_comms=True, has_wr=False):
#        print("acq400_hapi.Acq2106 %s" % (_uut))
        Acq400.__init__(self, _uut, monitor=monitor, s0_client=s0_client)
        self.mb_clk_min = 100000
        sn_map = ()
        if has_comms:
            sn_map += (('cA', AcqSites.SITE_CA), ('cB', AcqSites.SITE_CB))
        if has_wr:
            sn_map += (('cC', AcqSites.SITE_CC), )
        if has_dsp:
            sn_map += (('s14', AcqSites.SITE_DSP),)

        for ( service_name, site ) in sn_map:
            try:
                self.svc[service_name] = netclient.Siteclient(self.uut, AcqPorts.SITE0+site)
            except socket.error:
                print("uut {} site {} not populated".format(_uut, site))
            self.mod_count += 1

    def set_mb_clk(self, hz=4000000, src="zclk", fin=1000000):
        print("set_mb_clk {} {} {}".format(hz, src, fin))
        Acq400.set_mb_clk(self, hz, src, fin)
        try:
            self.s0.SYS_CLK_DIST_CLK_SRC = 'Si5326'
        except AttributeError:
            print("SYS_CLK_DIST_CLK_SRC, deprecated")
        self.s0.SYS_CLK_OE_CLK1_ZYNQ = '1'

    def set_sync_routing_slave(self):
        Acq400.set_sync_routing_slave(self)
        self.s0.SYS_CLK_OE_CLK1_ZYNQ = '1'

    def set_master_trg(self, trg, edge = "rising", enabled=True):
        if trg == "fp":
            self.s0.SIG_SRC_TRG_0 = "EXT" if enabled else "HOSTB"
        elif trg == "int":
            self.s0.SIG_SRC_TRG_1 = "STRIG"


    def set_MR(self, enable, evsel0=4, evsel1=5, MR10DEC=8):
        if enable:
            self.s1.ACQ480_MR_EVSEL_0 = 'd{}'.format(evsel0)
            self.s1.ACQ480_MR_EVSEL_1 = 'd{}'.format(evsel1)
            self.s1.ACQ480_MR_10DEC = 'dec{}'.format(MR10DEC)
            self.s1.ACQ480_MR_EN = '1'
        else:
            self.s1.ACQ480_MR_EN = '0'
    def wr_PPS_active(self):
        if self.cC.WR_PPS_ACTIVE.split(' ')[1] == '1.0':
            return True
        else:
            pps0 = self.cC.WR_PPS_COUNT.split(' ')[1]
            time.sleep(2)
            pps1 = self.cC.WR_PPS_COUNT.split(' ')[1]
            return pps0 != pps1


    def get_sys_info(self):
        """
        Returns a string of system information to
        """
        line = "{: <6}{: <16}{: <35}{: <16}\n"
        from datetime import datetime
        info = ""
        info += "="*72 + "\n"
        info += datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
        info += "FPGA: {}\n".format(self.s0.fpga_version)
        info += "FW:   {}\n\n".format(self.s0.software_version)
        info += "MB Info:\n"
        info += "{: <57}{: <16}\n".format("MODEL", "SERIAL")
        info += "{: <57}{: <16}\n\n".format(self.s0.MODEL, self.s0.SERIAL)
        info += "-" * 72 + "\n\n"
        info += "Site Info:\n"
        info += line.format("SITE", "MODEL", "PART_NUM", "SERIAL")
        for site in self.sites:
            info += line.format(site,
                                self.svc["s{}".format(site)].MODEL,
                                self.svc["s{}".format(site)].PART_NUM,
                                self.svc["s{}".format(site)].SERIAL)
        info += "="*72
        return info


class Acq2106_Mgtdram8(Acq2106):
    MGT_BLOCK_BYTES = 0x400000
    MGT_BLOCK_MULTIPLE = 16

    def __init__(self, uut, monitor=True, s0_client=None):
#        print("acq400_hapi.Acq2106_MgtDram8 %s" % (uut))
        Acq2106.__init__(self, uut, monitor=monitor, s0_client=s0_client, has_dsp=True)

    def run_mgt(self, filter = null_filter, set_arm=True):
        pm = ProcessMonitor(self, AcqPorts.MGTDRAM, filter, set_arm)
        while pm.quit_requested != True:
            time.sleep(1)

    def create_mgtdram_pull_client(self):
        return MgtDramPullClient(self.uut)


class Acq2106_TIGA(Acq2106):
   
    def __init__(self, uut, monitor=True, s0_client=None):
        print("acq400_hapi.Acq2106_TIGA %s" % (uut))
        Acq2106.__init__(self, uut, monitor=monitor, s0_client=s0_client, has_wr=True)
        self.pg_sites = [ sx for sx in range(1,6+1) if sx in self.sites and self.svc["s{}".format(sx)].MTYPE == '7B' ]
            
    def load_dio482pg(self, site, stl, trace = False):
        self.load_stl(stl, AcqPorts.DIO482_PG_STL+site*10, trace)
        
    def set_DO(self, site, dox, value = 'P'):
        self.svc["s{}".format(site)].set_knob("DO_{}".format(dox), value)
    

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
        print("SITE:%s MODEL:%s" % (sx, uut.svc[sx].sr("MODEL")))


def sigsel(enable=1, dx=1, site=None, edge=1):
    if not site is None:
        return "{},{},{}".format(enable, site+1, edge)
    else:
        return "{},{},{}".format(enable, dx, edge)


def factory(_uut):
    ''' instantiate s0. deduce what sort of ACQ400 this is and invoke the appropriate subclass
    '''
    try:
        cached = Acq400.uuts[_uut]
        return cached
    except KeyError:
        pass
    
    s0 = netclient.Siteclient(_uut, AcqPorts.SITE0)
    
    if not s0.MODEL.startswith("acq2106"):
        return Acq400(_uut, s0_client=s0)
    
    # here with acq2106
    
    try:
        if s0.is_tiga != "none":
            return Acq2106_TIGA(_uut, s0_client=s0)
        if s0.has_mgt != "none" and s0.has_mgtdram != "none":
            return Acq2106_Mgtdram8(_uut, s0_client=s0)
           
        has_dsp = s0.has_dsp != "none"
        has_wr = s0.has_wr != "none"
        has_sfp = s0.has_mgt != "none"
        
       
        return Acq2106(_uut, s0_client=s0,  has_dsp=has_dsp, has_comms=has_sfp, has_wr=has_wr)
    except:
        ''' nothing special, make it a default class with existing s0
        '''
        print("Factory method encountered a problem. Most likely target system"
              "\nFW is older than necessary. Using default acq2106 settings.\n")
        return Acq2106(_uut, s0_client=s0)
    
def get_hapi():
    ''' find instance of hapi '''
    return os.path.dirname(os.path.dirname(__file__))

def freq(sig):
    return float(sig.split(" ")[1])

def intpv(pv):
    return int(pv.split(" ")[1])

def pv(pv):
    return pv.split(" ")[1]
       
if __name__ == '__main__':
    run_unit_test()
