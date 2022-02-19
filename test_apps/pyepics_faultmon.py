#!/usr/bin/env python3


import argparse
import epics
import time
import acq400_hapi
import sys


class PV_logger(epics.PV):
    def __init__(self, pv):
        epics.PV.__init__(self, pv)
        self.pvname = pv

    def put(self, value):
        print("{}.put({})".format(self.pvname, value))
        super().put(value)

    def get(self, verbose=True):
        value = super().get()
        if verbose:
            print("{}.get() => {}".format(self.pvname, value))
        return value

def pv_factory(uut):
    def _pv_factory(pv):
        return PV_logger("{}:{}".format(uut, pv))
    return _pv_factory


def config_faultmon(args, PVF):
    uut = args.uuts[0]
    pv_pre = PVF("MODE:TRANSIENT:PRE")
    pv_pre.put(args.pre)

    pv_post = PVF("MODE:TRANSIENT:POST")
    pv_post.put(args.post)

    pv_tran = PVF("MODE:TRANSIENT")
    pv_tran.put(1)

    pass

def offload_channels(args):
    try:
        sc = args.sc
    except:
        uuts = [ acq400_hapi.factory(u) for u in args.uuts ]
        sc = acq400_hapi.ShotControllerWithDataHandler(uuts, args)
        args.sc = sc
    sc.handle_data(args)

def run_faultmon(args):
    uut = args.uuts[0]
    PVF = pv_factory(uut)
    ca_test = PVF("0:SERIAL").get()
    if not ca_test:
        print("ERROR: ca is not working. Maybe need to set EPICS_CA_ADDR_LIST?, eg, assuming you have DNS")
        print("export EPICS_CA_ADDR_LIST={}".format(args.uuts[0]))
        sys.exit(1)
    print("Testing CA: SERIAL:{}".format(ca_test))
    config_faultmon(args, PVF)
    pv_state = PVF("MODE:TRANS_ACT:STATE")
    pv_arm = PVF("MODE:TRANSIENT:SET_ARM")

    for shot in range(0, args.shots):
        print("shot {}".format(shot))
        pv_arm.put(1)

        while True:
            print("wait BUSY: ", end="")
            if pv_state.get() != 0:
                break
            time.sleep(0.5)        

        while True:
            print("wait IDLE: ", end="")
            if pv_state.get() == 0:
                break            
            time.sleep(1)

        if args.channels:
            offload_channels(args)

    return 0


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='PyEPICS faultmon example')
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    acq400_hapi.ShotControllerUI.add_args(parser)    
    parser.add_argument('--shots', default=1, type=int, help='number of shots to run')    
    parser.add_argument('uuts', nargs=1, help="uut")

    return parser.parse_args(argStr)



def main():
    return run_faultmon(get_args())



if __name__ == '__main__':
    main()
