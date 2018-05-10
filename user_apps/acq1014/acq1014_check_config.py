#!/usr/bin/env python

import sys
import acq400_hapi

def query_clocks(uut):
    print("query_clocks {}" .format(uut.uut))
    print("{:>10} {}".format("trg", uut.s1.trg))
    print("{:>10} {}".format("clk", uut.s1.clk))
    print("{:>10} {}".format("transient", uut.s0.transient))
    print("{:>10} {}".format("EXT FREQ", uut.s0.SIG_CLK_EXT_FREQ))
    print("{:>10} {}".format("CLK FREQ", uut.s0.SIG_CLK_MB_FREQ))
    print("{:>10} {}".format("TRG", uut.s0.SIG_TRG_EXT_COUNT))

def run_main():
    uuts = []
    if len(sys.argv) > 1:
        for addr in sys.argv[1:]:
            uuts.append(acq400_hapi.Acq400(addr))
    else:
        print("USAGE: acq1014_check_config UUT1 [UUT ...]")

    for uut in uuts:
        query_clocks(uut)    


if __name__ == '__main__':
    run_main()


