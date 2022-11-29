#!/usr/bin/env python3
""" hudp_setup.py : configure Hardware UDP 

hudp_setup.py [opts] TXUUT RXUUT

sets up a one way transfer from TXUUT to RXUUT

[pgm@hoy5 acq400_hapi]$  ./user_apps/acq2106/hudp_setup.py --help
usage: hudp_setup.py [-h] [--netmask NETMASK] [--tx_ip TX_IP] [--rx_ip RX_IP] [--gw GW] [--port PORT] [--run0 RUN0] 
                     [--play0 PLAY0] [--broadcast BROADCAST] [--disco DISCO] [--spp SPP]
                     [--hudp_decim HUDP_DECIM]
                     txuut rxuut

hudp_setup

positional arguments:
  txuut                 transmit uut
  rxuut                 transmit uut

options:
  -h, --help            show this help message and exit
  --netmask NETMASK     netmask (default: 255.255.255.0)
  --tx_ip TX_IP         tx ip address (default: 10.12.198.128)
  --rx_ip RX_IP         rx ip address (default: 10.12.198.129)
  --gw GW               gateway (default: 10.12.198.1)
  --port PORT           port (default: 53676)
  --run0 RUN0           set tx sites+spad (default: 1 1,16,0)
  --play0 PLAY0         set rx sites+spad (default: 1 16)
  --broadcast BROADCAST
                        broadcast the data (default: 0)
  --disco DISCO         enable discontinuity check at index x (default: None)
  --spp SPP             samples per packet (default: 1) 
  --hudp_decim HUDP_DECIM
                        hudp decimation, 1..16 (default: 1)

Increasing spp reduces the packet rate per sample, potentially enabling a higher sample rate (do NOT exceed MTU 1400 bytes)
Increasing decimation reduces the packet rate, suitable for spp=1 low latency control, while full rate data flows to DRAM for archive
The DISContinuity check is a packet data checker. 
    Typically, the TX data comes from ACQ2106 with SPAD enabled, and the DISCO index is SPAD[0], sample ramp.


If either TXUUT or RXUUT is NOT an ACQ2106, or has already been configured for one direction, specify "none"

Examples:

Send data from UUT acq2106_363 at tx_ip ip 10.12.198.128 to UUT acq2106_364 at rx_ip=10.12.198.129

./user_apps/acq2106/hudp_setup.py --rx_ip=10.12.198.128 --tx_ip 10.12.198.129 --run0='1 1,16,0' --play0='1 16' acq2106_363 acq2106_364

Send data from UUT acq2106_363 at tx_ip ip 10.12.198.128 to non-HUDP destination rx_ip=10.12.198.254

./user_apps/acq2106/hudp_setup.py --rx_ip=10.12.198.254 --tx_ip 10.12.198.128 --run0='1 1,16,0' acq2106_363 none

Send data from non-HUDP source at tx_ip 10.12.198.254 to UUT acq2106_363 at rx_ip  10.12.198.128

./user_apps/acq2106/hudp_setup.py --rx_ip=10.12.198.128 --tx_ip 10.12.198.254 --play0='1 16' none acq2106_363

In all cases, 
for UUT Tx, run0 specifies data from site1 followed by a 16 column ScratchPAD.
for UUT Rx, play0 specifues datas to site1 followed by a 16 column TrashCAN.

This allows, for example a 32 channel, 16 bit ADC to play data direct to a 32 channel DAC, 
including instrumentation that could be checked with --disco=16 (SPAD[0] at offset 16 LW)



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

def hudp_init(args, uut, ip):
    uut.s10.tx_ctrl = 9
    uut.s10.ip = ip
    uut.s10.gw = args.gw
    uut.s10.netmask = args.netmask
    if args.disco is not None:
        print("enable disco at {}".format(args.disco))
        uut.s10.disco_idx = args.disco
        uut.s10.disco_en  = 1
    else:
        uut.s10.disco_en = 0
    
def hudp_enable(uut):
    uut.s10.tx_ctrl = 1
    
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
def config_tx_uut(txuut, args):    
    print("txuut {}".format(txuut.uut))
    if args.run0 != 'notouch':
        txuut.s0.run0 = args.run0
    hudp_init(args, txuut, args.tx_ip)
    txuut.s10.hudp_decim = args.hudp_decim
    txuut.s10.src_port = args.port
    txuut.s10.dst_port = args.port
    txuut.s10.dst_ip = args.rx_ip if args.broadcast == 0 else ip_broadcast(args)

    if args.hudp_relay is not None:
        txuut.s10.udp_data_src = 1
        tx_ssb = int(txuut.s0.dssb) - args.hudp_relay
        txuut.s10.slice_len = tx_ssb//4
        txuut.s10.slice_off = args.hudp_relay//4
    else:
        txuut.s10.udp_data_src = 0
        tx_ssb = int(txuut.s0.ssb)

    txuut.s10.tx_sample_sz = tx_ssb
    txuut.s10.tx_spp = args.spp
    tx_pkt_sz = tx_ssb*args.spp                         # compute tx pkt sz and check bounds
    if  tx_pkt_sz > MTU:
        print("ERROR packet length {} exceeds MTU {}".format(tx_pkt_sz, MTU))
    hudp_enable(txuut)
    tx_calc_pkt_sz = int(txuut.s10.tx_calc_pkt_sz)      # actual tx pkt sz computed by FPGA logic.
    if tx_pkt_sz != tx_calc_pkt_sz:
        print("ERROR: set tx_pkt_size {} actual tx_pkt_size {}".format(tx_pkt_sz, tx_calc_pkt_sz))    
    print("TX configured. ssb:{} spp:{} tx_pkt_size {}".format(tx_ssb, args.spp, tx_pkt_sz))

# rx: XO : AO, DO        
def config_rx_uut(rxuut, args):
    print("rxuut {}".format(rxuut.uut))
       
    if args.play0 != 'notouch':
        rxuut.s0.play0 = args.play0       
    rxuut.s0.distributor = 'comms=U off'        
    rxuut.s0.distributor = 'on'

    hudp_init(args, rxuut, args.rx_ip)
    rxuut.s10.rx_src_ip = args.tx_ip
    rxuut.s10.rx_port = args.port
    hudp_enable(rxuut)    
    
def run_main(args):
    if args.txuut[0] != "none":
        config_tx_uut(acq400_hapi.factory(args.txuut[0]), args)
    if args.rxuut[0] != "none":
        config_rx_uut(acq400_hapi.factory(args.rxuut[0]), args)


def ui():
    parser = argparse.ArgumentParser(description="hudp_setup", 
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--netmask", default='255.255.255.0', help='netmask')
    parser.add_argument("--tx_ip",   default='10.12.198.128', help='tx ip address')
    parser.add_argument("--rx_ip",   default='10.12.198.129', help='rx ip address')
    parser.add_argument("--gw",      default='10.12.198.1',   help='gateway')
    parser.add_argument("--port",    default='53676',         help='port')
    parser.add_argument("--run0",    default='1 1,16,0',      help="set tx sites+spad or notouch if set elsewhere")
    parser.add_argument("--play0",   default='1 16',          help="set rx sites+spad or notouch if set elsewhere")
    parser.add_argument("--broadcast", default=0, type = int, help="broadcast the data")
    parser.add_argument("--disco",   default=None, type=int,  help="enable discontinuity check at index x")
    parser.add_argument("--hudp_relay", default=None, type=int,  help="0..N: relay LLC VI out HUDP txt offset in vector")
    parser.add_argument("--spp",     default=1, type=int,     help="samples per packet")
    parser.add_argument("--hudp_decim", default=1, type=int,  help="hudp decimation, 1..16")
    parser.add_argument("txuut", nargs=1,                     help="transmit uut")
    parser.add_argument("rxuut", nargs=1,                     help="transmit uut")
    return parser.parse_args()
    
if __name__ == '__main__':
    run_main(ui())





