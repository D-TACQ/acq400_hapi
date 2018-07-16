#!/usr/bin/python
"""
	acq1001_local_clk_embedded_event.py

	python acq1001_local_clk_embedded_event.py UUT

        - set site 1 to run at 2MHz from MB_CLK
        - enable event1 from front panel	
"""

import sys

try:
    addr = sys.argv[1]
    print("UUT {}".format(addr))
except IndexError:
    print("Usage: python acq1001_local_clk_embedded_event.py UUT")
    sys.exit(1)


import acq400_hapi
uut = acq400_hapi.Acq400(addr)
uut.s1.bank_mask='AB'
uut.s1.event1='1,0,1'
# sugar to make the GUI behave
uut.s1.EVENT1='enable'
uut.s1.trg='1,0,1'
uut.s0.SYS_CLK_FPMUX='FPCLK'
uut.s0.SIG_CLK_MB_FIN='2000000'
# ics527 min output 4MHz
uut.s0.SIG_CLK_MB_SET='4000000'

uut.s1.clk='1,0,1'
uut.s1.CLK_DX='d0'
uut.s1.CLKDIV=2


