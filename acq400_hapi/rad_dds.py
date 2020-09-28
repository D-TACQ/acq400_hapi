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


class AD9854:
    class CR:
        regular_en = '004C0061'
        chirp_en   = '004C8761'
    
    @staticmethod
    def ftw2ratio(ftw):
        return float(int('0x{}'.format(ftw), 16)/float(0x1000000000000))
    
    @staticmethod
    def ratio2ftw(ratio):
        return format(int(ratio * pow(2, 48)), '012x')  
      
class RAD3DDS(acq400.Acq400):
    
    @staticmethod
    def ftw2ratio(ftw):
        return AD9854.ftw2ratio(ftw)
    
    
    @staticmethod
    def ratio2ftw(ratio):
        return AD9854.ratio2ftw(ratio)
    
    def radcelf_init(self):
        # port of original RADCELF_init shell script
    #Reset the entire clock chain
        self.s2.clkd_hard_reset = 1
        self.s2.clkd_hard_reset = 0

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
        self.clkdA.DIV0     = '1100'
        self.clkdA.DIV1     = '1100'
        self.clkdA.DIV2     = '1100'
        self.clkdA.DIV3     = '1100'
        self.clkdA.DIV4     = '1100'
        self.clkdA.UPDATE   = 1
        
        # set clkdB to pass-thru
        self.clkdB.DIV0     = '0080'
        self.clkdB.DIV1     = '0080'
        self.clkdB.DIV2     = '0080'
        self.clkdB.DIV3     = '0080'
        self.clkdB.DIV4     = '0080'
        self.clkdB.UPDATE   = 1
        
# Reset the DDS
        self.s2.ddsX_hard_reset = 1
        self.s2.ddsX_hard_reset = 0
    
#Switch the clocks off on the DDS Devices to stop I/O Updates

#Clock Remapping DDS - Device clkA Output 1
        self.clkdA.LVPECL1  = '0a'
        self.clkdA.UPDATE   = '01'

#The two Main DDS devices on device clkB Outputs 0 and 1
        self.clkdB.LVPECL0  = '0a'
        self.clkdB.LVPECL1  = '0a'
        self.clkdB.UPDATE   = 1

#Write to the Control Registers on the 3 DDS devices - 
# External I/O Update and SDO On
# Set the RefClk Multiplier on at x4 switch off the Inverse Sinc Filter
        self.ddsA.CR = '00440041'
        self.ddsB.CR = '00440041'
        self.ddsC.CR = '00440041'

#Switch the Clocks back on again
        self.clkdA.LVPECL1 = '08'
        self.clkdA.LVPECL0 = '08'
        self.clkdB.LVPECL1 = '08'
        self.clkdB.LVPECL0 = '08'
        self.clkdA.UPDATE  = 1
        self.clkdB.UPDATE  = 1

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