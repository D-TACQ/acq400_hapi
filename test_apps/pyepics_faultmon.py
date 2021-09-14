#!/usr/bin/env python3


import argparse
import epics
import time


def pv_factory(uut):
    def _pv_factory(pv):
        return epics.PV("{}:{}".format(uut, pv))
    return _pv_factory


def config_faultmon(args, PVF):
    uut = args.uut[0]
    pv_pre = PVF("MODE:TRANSIENT:PRE")
    pv_pre.put(args.pre)

    pv_post = PVF("MODE:TRANSIENT:POST")
    pv_post.put(args.post)

    pv_tran = PVF("MODE:TRANSIENT")
    pv_tran.put(1)
    pass

def run_faultmon(args):
    uut = args.uut[0]
    PVF = pv_factory(uut)
    config_faultmon(args, PVF)
    pv_state = PVF("MODE:TRANS_ACT:STATE")
    pv_arm = PVF("MODE:TRANSIENT:SET_ARM")
    pv_trg0_src = PVF("0:SIG:SRC:TRG:0")
    for shot in range(0, args.shots):
        print("shot {}".format(shot))
        pv_trg0_src.put("NONE")
        pv_arm.put(1)
        time.sleep(20)
        pv_trg0_src.put("EXT")
        while pv_state.get() != "IDLE":
            print("wait IDLE")
            time.sleep(1)

        



    return 0
#    uut = args.uuts[0]


    return None


def get_args(argStr=None):
    parser = argparse.ArgumentParser(description='PyEPICS faultmon example')

    parser.add_argument('--pre', default=50000, type=int, help='pre samples')
    parser.add_argument('--post', default=50000, type=int, help='post samples')
    parser.add_argument('--shots', default=1, type=int, help='number of shots to run')
    parser.add_argument('uut', nargs=1, help="uut")

    return parser.parse_args(argStr)



def main():
    return run_faultmon(get_args())



if __name__ == '__main__':
    main()
