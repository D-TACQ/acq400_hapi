#!/usr/bin/env python3

import acq400_hapi
import argparse
import threading
import time

"""
Usage:
./user_apps/acq400/sync_cluster.py --masters=acq2206_010,acq2206_007 \
    --slaves=acq2206_009,acq2206_008,acq2206_006,acq2206_005 \
    --fclk=20M --fin=1M --clk_route=HDMI --trg_route=HDMI

"""

def run_main(args):

    if not args.toprole:
        if args.clk_route not in routing:
            exit('Invalid toprole')
        args.toprole = routing[args.clk_route]['role']

    uuts = []
    for uutname in args.masters:
        role = 'master'
        uuts.append((uutname, role))

    for uutname in args.slaves:
        role = 'slave'
        uuts.append((uutname, role))

    config_uuts(uuts, args)
    print('Done')

def config_uuts(uuts, args):
    def thread_wrapper(uut_item, args):
        uutname = uut_item[0]
        role = uut_item[1]
        print(f"Configuring {uutname} as {role}")

        try:
            uut = acq400_hapi.factory(uutname)
            uut.is_master = True if role == 'master' else False
        except Exception as e:
            exit(print(f"Error unable to connect to {uutname}"))

        if args.run_sync_role:
            if uut.is_master:
                role = args.toprole
            cmd = f"{role} {args.fclk} {args.fin}"
            print(f"Sync_role: {uutname} {cmd}")
            uut.s0.sync_role = cmd
            time.sleep(5)

        if args.clk_route in routing:
            print(f"CLK routing: {uutname} {args.clk_route}")
            routing[args.clk_route]['clk_func'](uut)

        if args.trg_route in routing:
            print(f"TRG routing: {uutname} {args.trg_route}")
            routing[args.trg_route]['trg_func'](uut)

        if args.gpio_to_trg:
            print(f"GPIO to TRG: {uutname} {args.gpio_to_trg}")
            route_hdmi_to_d1(uut)

        if args.rtm:
            print(f"Enable RTM: {uutname} rtm_translen{args.rtm_translen}")
            setup_rtm(uut, args)

        if args.TRG_DX:
            uut.s1.TRG_DX = args.TRG_DX

    threads = []
    for uut_item in uuts:
        thread = threading.Thread(target=thread_wrapper, args=(uut_item, args))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

def route_MASTER_clk(uut):
    if not uut.is_master:
        uut.s0.SIG_SRC_CLK_0 = 'HDMI'
        uut.s0.SYS_CLK_FPMUX = 'ZCLK'
        uut.s0.SIG_ZCLK_SRC = 'CLK.d0'
    if uut.is_master:
        uut.s0.SIG_SRC_CLK_0 = 'INT01M'
        uut.s0.SIG_SYNC_OUT_CLK_DX = 'd0'

def route_HDMI_clk(uut):
    uut.s0.SIG_SRC_CLK_0 = 'HDMI'
    uut.s0.SYS_CLK_FPMUX = 'ZCLK'
    uut.s0.SIG_ZCLK_SRC = 'CLK.d0'
    if uut.is_master:
        uut.s0.SIG_SYNC_OUT_CLK_DX = 'd0'

def route_FP_clk(uut):
    if not uut.is_master:
        uut.s0.SYS_CLK_FPMUX = 'ZCLK'
        uut.s0.SIG_ZCLK_SRC = 'CLK.d0'
        uut.s0.SIG_SRC_CLK_0 = 'HDMI'
    if uut.is_master:
        uut.s0.SYS_CLK_FPMUX = 'FPCLK'
        uut.s0.SIG_SYNC_OUT_CLK_DX = 'd0'

def route_MASTER_trg(uut):
    #todo
    pass

def route_HDMI_trg(uut):
    uut.s0.SIG_SRC_TRG_0 = 'HDMI'
    if uut.is_master:
        uut.s0.SIG_SYNC_OUT_TRG_DX = 'd0'

def route_FP_trg(uut):
    uut.s0.SIG_SRC_TRG_0 = 'HDMI'
    if uut.is_master:
        uut.s0.SIG_SRC_TRG_0 = 'EXT'
        uut.s0.SIG_SYNC_OUT_TRG_DX = 'd0'

def route_hdmi_to_d1(uut):
    uut.s0.SIG_SRC_TRG_1 = 'HDMI_GPIO'
    uut.s1.TRG_DX = 'd1'
    if uut.is_master:
        uut.s0.SIG_EVENT_SRC_1 = 'HDMI_GPIO'
        uut.s0.SIG_SYNC_OUT_GPIO = 'EVNT'
        uut.s0.SIG_SYNC_OUT_GPIO_DX = 'd1'

def setup_rtm(uut, args):
    uut.s1.RGM = 'RTM'
    uut.s1.RGM_DX = args.rtm
    uut.s1.RGM_SENSE = 'rising'
    if args.rtm_translen:
        uut.s1.RTM_TRANSLEN = args.rtm_translen

routing = {
    'MASTER' : {
        'role'  : 'master',
        'clk_func' :  route_MASTER_clk,
        'trg_func' :  route_MASTER_trg,
    },
    'HDMI' : {
        'role'  : 'rpmaster',
        'clk_func' :  route_HDMI_clk,
        'trg_func' :  route_HDMI_trg,
    },
    'FP' : {
        'role'  : 'fpmaster',
        'clk_func' :  route_FP_clk,
        'trg_func' :  route_FP_trg,
    }
}

"""
clk routing:
        MASTER               MASTER ->HDMI->  SLAVE
        HDMI    EXT ->HDMI-> MASTER ->HDMI->  SLAVE
        FP      EXT ->FP->   MASTER ->HDMI->  SLAVE

trg routing:
        MASTER  todo
        HDMI    EXT ->HDMI-> MASTER ->HDMI->  SLAVE
        FP      EXT ->FP->   MASTER ->HDMI->  SLAVE
"""

def list_of_strings(string):
    return string.split(',')

def get_parser():
    parser = argparse.ArgumentParser(description='Setup cluster of uuts')
    parser.add_argument('--run_sync_role', default=1, type=int, help="run sync role")
    parser.add_argument('--fclk', default='20M', help="sample clock rate")
    parser.add_argument('--fin',  default='1M', help="external clock rate")
    parser.add_argument('--clk_route', help="clock routing MASTER, HDMI or FP")
    parser.add_argument('--trg_route', help="trigger routing HDMI or FP")
    parser.add_argument('--rtm', default=None, help="Enable rtm and set TRG to passed value ie d0")
    parser.add_argument('--rtm_translen', default=None, type=int, help="rtm_translen value to set")
    parser.add_argument('--gpio_to_trg', default=None, help="Routes hdmi_gpio to passed trg ie d1")#TRG:DX
    parser.add_argument('--TRG_DX', default=None, help="Set 1:TRG:DX source")
    parser.add_argument('--toprole', default=None, help="role to use for the masters")
    parser.add_argument('--masters', required=True, type=list_of_strings, help="master uuts")
    parser.add_argument('--slaves', required=True, type=list_of_strings, help="slave uuts")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())