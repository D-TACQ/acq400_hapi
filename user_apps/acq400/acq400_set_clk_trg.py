#!/usr/bin/python


"""
A script to configure a UUT as master or slave depending on the position of the
HDMI cable in the system.

Use case 1: Run on a specific UUT locally.
Use case 2: Run remotely from a host by providing a UUT argument.
"""


import acq400_hapi
import argparse
import socket


def set_clk_trg(args):
    try:
        uut = acq400_hapi.Acq400(args.uut)
    except:
        print "Connection refused. If you are running this script from " \
              "a remote host then make sure you provide a uut argument."
    # Check if master or slave
    if uut.s0.SIG_SYNC_BUS_OUT_CABLE_DET.split(" ")[-1] == "CONNECTED":
        print "Configuring as master."
        uut.s0.SIG_SYNC_OUT_CLK = "CLK"
        uut.s0.SIG_SYNC_OUT_CLK_DX = "d3"
        uut.s0.SIG_SYNC_OUT_TRG = "TRG"
        uut.s0.SIG_SYNC_OUT_TRG_DX = args.trg
        uut.s0.SIG_SYNC_OUT_SYNC = "SYNC"
        uut.s0.SIG_SYNC_OUT_SYNC_DX = "d2"
        uut.s1.clk = "1,3,1"
        uut.s1.trg = "1,",args.trg,",1"
        uut.s1.sync = "0,0,0"
        uut.s1.clkdiv = 1
        uut.s1.sync_trg_to_clk=1

    else:
        print "Configuring as slave"
        uut.s0.SIG_SRC_CLK_0 = "EXT"
        uut.s0.SIG_SRC_CLK_1 = "HDMI"
        uut.s0.SIG_SRC_TRG_0 = "HDMI"
        uut.s0.SIG_SRC_SYNC_0 = "HDMI"
        uut.s0.SIG_SYNC_OUT_CLK = "CLK"
        uut.s0.SIG_SYNC_OUT_CLK_DX = "d1"
        uut.s0.SIG_SYNC_OUT_TRG = "TRG"
        uut.s0.SIG_SYNC_OUT_TRG_DX = "d0"
        uut.s0.SIG_SYNC_OUT_SYNC = "SYNC"
        uut.s0.SIG_SYNC_OUT_SYNC_DX = "d0"
        uut.s1.clk = "1,0,1"
        uut.s1.trg = "1,0,1"
        uut.s1.sync = "1,0,1"
        uut.s1.sync_trg_to_clk=0


def run_main():
    parser = argparse.ArgumentParser(description = 'set clk trg')
    parser.add_argument('--trg', type=str, default="d2",
    help="Which trigger to use. Default is soft.")
    parser.add_argument('--uut', type=str, default=socket.gethostname(),
    help='Which UUT we are working with. Default is found using socket.')
    args = parser.parse_args()
    set_clk_trg(args)

if __name__ == '__main__':
    run_main()
