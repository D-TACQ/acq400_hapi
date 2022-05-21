#!/usr/bin/env python
""" hudp_setup.py : configure Hardware UDP 

hudp_setup.py [opts] TXUUT RXUUT

opts:
"""

import argparse
import acq400_hapi
import time
import sys
if sys.version_info < (3, 0):
    from future import builtins
    from builtins import input

def hdup_init(args, uut, ip):
    uut.s10.ctrl = 9
    uut.s10.ip = ip
    uut.s10.gw = args.gw
    uut.s10.netmask = args.netmask
    
def hdup_enable(uut):
    uut.s10.ctrl = 1
       
def run_main(args):
    txuut = acq400_hapi.factory(args.txuut[0])
    rxuut = acq400_hapi.factory(args.rxuut[0])
    print("txuut {}".format(txuut.uut))
    print("rxuut {}".format(rxuut.uut))
    
    print("txuut assume aggregator, capture has been set up")
    hdup_init(args, txuut, args.tx_ip)
    txuut.s10.src_port = args.port
    txuut.s10.dst_port = args.port
    txuut.s10.dst_ip = args.rx_ip
    txuut.s10.tx_pkt_sz = txuut.s0.ssb
    hdup_enable(txuut)
       
    print("rxuut assume play sites pad done {}".format(rxuut.s0.distributor))
    rxuut.s0.distributor = 'comms=U off'             
    rxuut.s0.distributor = 'on'

    hdup_init(args, rxuut, args.rx_ip)
    rxuut.s10.rx_src_ip = args.tx_ip
    rxuut.s10.rx_port = args.port
    hdup_enable(rxuut)

    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="hdup_setup")
    parser.add_argument("--netmask", default='255.255.255.0', help='netmask, default 255.255.255.0')
    parser.add_argument("--tx_ip",   default='10.12.198.128')
    parser.add_argument("--rx_ip",   default='10.12.198.129')
    parser.add_argument("--gw",      default='10.12.198.1')
    parser.add_argument("--port",    default='53676')
    parser.add_argument("txuut", nargs=1, help="transmit uut")
    parser.add_argument("rxuut", nargs=1, help="transmit uut")
    run_main(parser.parse_args())





