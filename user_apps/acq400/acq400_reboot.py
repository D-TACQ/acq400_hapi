#!/usr/bin/env python

"""
Reboot acq400 system

USAGE: acq400_reboot UUT1 [UUT ...]
"""

import sys
import acq400_hapi

def run_main():
    uuts = []
    if len(sys.argv) > 1:
        for addr in sys.argv[1:]:
            uuts.append(acq400_hapi.Acq400(addr))
    else:
        print("USAGE: acq400_reboot UUT1 [UUT ...]")

    for uut in uuts:
        uut.s0.reboot = "3210"


if __name__ == '__main__':
    run_main()


