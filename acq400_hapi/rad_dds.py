#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
raddds.py specializes Acq400 for RADCELF triple DDS device

- enumerates all site services, available as uut.sX.knob
- simply property interface allows natural "script-like" usage

 - eg
  - uut1.s0.set_arm = 1
 - compared to 
  - set.site1 set_arm=1

- monitors transient status on uut, provides blocking events
- read_channels() - reads all data from channel data service.
Created on Sun Jan  8 12:36:38 2017

@author: pgm
"""

from . import acq400
from . import netclient
from builtins import staticmethod


class AD9854:
    class CR:
        regular_en = '0061'
        chirp_en   = '8761'
        low_power  = '0041'
        
    @staticmethod
    # CR for clock * n
    def CRX(n = 4, chirp=False):            
        return '{:08x}'.format(int(n << 16) | int(AD9854.CR.chirp_en if chirp else AD9854.CR.regular_en, 16))
        
    @staticmethod
    # UCR for chirps_per_sec
    def UCR(chirps_per_sec, intclk=299999999):
        return '{:08x}'.format(int(intclk/2/chirps_per_sec))
        
    
    @staticmethod
    def ftw2ratio(ftw):
        return float(int('0x{}'.format(ftw), 16)/float(0x1000000000000))
    
    @staticmethod
    def ratio2ftw(ratio):
        return format(int(ratio * pow(2, 48)), '012x')  
    
    @staticmethod
    def CRX_chirp_off(n = 4):
        return '{:08x}'.format(int(n << 16) | int(AD9854.CR.low_power, 16))
  
class AD9512:
    class DIVX:
        div4 = '1100'
        passthru = '0080'
        
    @staticmethod
    def setDIVX(clkd, value):
        clkd.DIV0     = value
        clkd.DIV1     = value
        clkd.DIV2     = value
        clkd.DIV3     = value
        clkd.DIV4     = value
        clkd.UPDATE   = '01'
        
    @staticmethod
    def clocksON(clkd):        
        clkd.LVPECL1 = '08'
        clkd.LVPECL0 = '08'
        clkd.UPDATE  = '01'
         
class RAD3DDS(acq400.Acq400):
    
    @staticmethod 
    def best_clock_pps_sync(fs):
        return fs//512 * 512;
    
    @staticmethod
    def ftw2ratio(ftw):
        return AD9854.ftw2ratio(ftw)
    
    
    @staticmethod
    def ratio2ftw(ratio):
        return AD9854.ratio2ftw(ratio)
    
    @staticmethod
    def pulse(knob):
        knob = 1
        knob = 0
    
    def chirp_freq(self, idds):
        return acq400.Acq400.freq(self.s0.get_knob('SIG_TRG_S2_FREQ' if idds==0 else 'SIG_TRG_S3_FREQ'))
    
    def radcelf_init(self):
        # port of original RADCELF_init shell script
    #Reset the entire clock chain
        RAD3DDS.pulse(self.s2.clkd_hard_reset)
        
        self.clkdA.CSPD     = '00'
        self.clkdA.UPDATE   = '01'

# Set Primary Clock LVPECL 2 Off, set LVDS 3 to Off, Set LVDS 4 to TTL
        self.clkdA.LVPECL2  = '0a'
        self.clkdA.LVDS3    = '01'
        self.clkdA.LVDS4    = '08'
        self.clkdA.UPDATE   = '01'

# Set Secondary Clock LVPECL 2 Off, set LVDS 3 to TTL
        self.clkdB.LVPECL2  = '0a'
        self.clkdB.LVDS3    = '08'
        self.clkdB.UPDATE   = '01'
#Set all the clkdA AD9512 dividers to divide by 4 to avoid overheat
#100MHz / 4 = 25Mhz source clock
        AD9512.setDIVX(self.clkdA, AD9512.DIVX.div4)       
        # set clkdB to pass-thru
        AD9512.setDIVX(self.clkdB, AD9512.DIVX.passthru)
            
# Reset the DDS
        RAD3DDS.pulse(self.s2.ddsX_hard_reset)
    
#Switch the clocks off on the DDS Devices to stop I/O Updates

#Clock Remapping DDS - Device clkA Output 1
        self.clkdA.LVPECL1  = '0a'
        self.clkdA.UPDATE   = '01'

#The two Main DDS devices on device clkB Outputs 0 and 1
        self.clkdB.LVPECL0  = '0a'
        self.clkdB.LVPECL1  = '0a'
        self.clkdB.UPDATE   = '01'

# Write to the Control Registers on the 3 DDS devices - 
# External I/O Update and SDO On
# Set the RefClk Multiplier on at x4 switch off the Inverse Sinc Filter
        self.ddsA.CR = AD9854.CR.low_power
        self.ddsB.CR = AD9854.CR.low_power
        self.ddsC.CR = AD9854.CR.low_power

#Switch the Clocks back on again
        AD9512.clocksON(self.clkdA)
        AD9512.clocksON(self.clkdB)

# tell FPGA to take over the clocking
        self.s2.ddsA_upd_clk_fpga = 1
        self.s2.ddsB_upd_clk_fpga = 1
        self.s2.ddsC_upd_clk_fpga = 1

        self.ddsA.strobe_mode = 1
        self.ddsB.strobe_mode = 1
        self.ddsC.strobe_mode = 1
        

    def __init__(self, _uut, monitor=True):
            acq400.Acq400.__init__(self, _uut, monitor)
            site = 4
            for sm in [ 'ddsA', 'ddsB', 'ddsC']:                
                self.svc[sm] = netclient.Siteclient(self.uut, acq400.AcqPorts.SITE0+site)
                self.mod_count += 1
                site += 1
            site = 7
            for sm in [ 'clkdA', 'clkdB']:
                self.svc[sm] = netclient.Siteclient(self.uut, acq400.AcqPorts.SITE0+site)
                self.mod_count += 1
                site += 1                