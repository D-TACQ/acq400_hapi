#!/usr/bin/env python
""" hudp_setup.py : configure Hardware UDP 

hudp_setup.py [opts] TXUUT RXUUT

opts:


pgm@hoy5 acq400_hapi]$ cat /home/pgm/PROJECTS/ACQ400/ACQ420FMC/NOTES/HUDPDEMO.txt
#!/bin/bash
set -x
TX1=${TX1:-acq2106_189} 
RX1=${RX1:-acq2106_274}
RX2=${RX2:-acq2106_130}
IP_TX1=${IP_TX1:-10.12.198.128}
IP_RX1=${IP_RX1:-10.12.198.129}
IP_RX2=${IP_RX2:-10.12.198.130}

echo HUDP Demo TX1:$TX1,$IP_TX1 RX1:$RX1,$IP_RX1 RX2:$RX2,$IP_RX2
echo set clk/trg
./user_apps/acq400/sync_role.py --fin=50k --fclk=50k --si5326_bypass 1 --toprole=fpmaster,strg acq2106_189
echo 'UNICAST ->' $RX1
./user_apps/acq2106/hudp_setup.py --tx_ip $IP_TX1 --rx_ip $IP_RX1 --broadcast=0 $TX1 $RX1
read continue
echo 'UNICAST ->' $RX2
./user_apps/acq2106/hudp_setup.py --tx_ip $IP_TX1 --rx_ip $IP_RX2 --broadcast=0 $TX1 $RX2
echo 'BROADCAST ->' $RX1 $RX2 and naboo
./user_apps/acq2106/hudp_setup.py --tx_ip $IP_TX1 --rx_ip $IP_RX1 --broadcast=1 $TX1 $RX1
./user_apps/acq2106/hudp_setup.py --tx_ip $IP_TX1 --rx_ip $IP_RX2 --broadcast=1 $TX1 $RX2

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
    if args.disco is not None:
        print("enable disco at {}".format(args.disco))
        uut.s10.disco_idx = args.disco
        uut.s10.disco_en  = 1
    else:
        uut.s10.disco_en = 0
    
def hdup_enable(uut):
    uut.s10.ctrl = 1
    
def ip_broadcast(args):
    ip_dest = args.rx_ip.split('.')
    nm = args.netmask.split('.')
    
    for ii in range(3,0,-1):
        if nm[ii] != '0':
            break
        else:
            ip_dest[ii] = '255'
    
    return '.'.join(ip_dest)
        
MTU = 1400

# tx: XI : AI, DI       
def config_tx_uut(args):
    txuut = acq400_hapi.factory(args.txuut[0])
    print("txuut {}".format(txuut.uut))
    txuut.s0.run0 = args.run0
    hdup_init(args, txuut, args.tx_ip)
    txuut.s10.src_port = args.port
    txuut.s10.dst_port = args.port
    txuut.s10.dst_ip = args.rx_ip if args.broadcast == 0 else ip_broadcast(args)   
    txuut.s10.tx_sample_sz = txuut.s0.ssb
    txuut.s10.tx_spp = args.spp
    if int(txuut.s0.ssb)*args.spp > MTU:
        print("ERROR packet length {} exceeds MTU {}".format(txuut.s10.tx_sample_sz*args.spp, MTU))
    hdup_enable(txuut)

# rx: XO : AO, DO        
def config_rx_uut(args):
    rxuut = acq400_hapi.factory(args.rxuut[0])
    print("rxuut {}".format(rxuut.uut))
        
    rxuut.s0.play0 = args.play0       
    rxuut.s0.distributor = 'comms=U off'        
    rxuut.s0.distributor = 'on'

    hdup_init(args, rxuut, args.rx_ip)
    rxuut.s10.rx_src_ip = args.tx_ip
    rxuut.s10.rx_port = args.port
    hdup_enable(rxuut)    
    
def run_main(args):
    if args.txuut[0] != "none":
        config_tx_uut(args)
    if args.rxuut[0] != "none":
        config_rx_uut(args)


def ui():
    parser = argparse.ArgumentParser(description="hdup_setup", 
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--netmask", default='255.255.255.0', help='netmask')
    parser.add_argument("--tx_ip",   default='10.12.198.128', help='rx ip address')
    parser.add_argument("--rx_ip",   default='10.12.198.129', help='tx ip address')
    parser.add_argument("--gw",      default='10.12.198.1',   help='gateway')
    parser.add_argument("--port",    default='53676',         help='port')
    parser.add_argument("--run0",    default='1 1,16,0',      help="set tx sites+spad")
    parser.add_argument("--play0",   default='1 16',          help="set rx sites+spad")
    parser.add_argument("--broadcast", default=0, type = int, help="broadcast the data")
    parser.add_argument("--disco",   default=None, type=int,  help="enable discontinuity check at index x")
    parser.add_argument("--spp",     default=1, type=int,     help="samples per packet")
    parser.add_argument("txuut", nargs=1,                     help="transmit uut")
    parser.add_argument("rxuut", nargs=1,                     help="transmit uut")
    return parser.parse_args()
    
if __name__ == '__main__':
    run_main(ui())





