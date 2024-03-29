#!/usr/bin/env python

"""acq400 looptest

where UUT1 is the ip-address or host name of first uut
example test client runs captures in a loop on one or more uuts

pre-requisite: UUT's are configured and ready to make a transient
capture
eg clk is running. soft trg enabled
eg transient length set.

.. rst-class:: hidden

    usage: acq400_caploop_rtrig.py [-h] [--trigger_uut TRIGGER_UUT]
                            [--nshots NSHOTS]
                            uuts [uuts ...]

    acq400 looptest

    positional arguments:
    uuts                  uuts

    optional arguments:
    -h, --help            show this help message and exit
    --trigger_uut TRIGGER_UUT  external trigger uut eg ACQ1001+DIO, soft_trigger brought to front panel
    --nshots NSHOTS       number of shots, default infinit


"""

import sys
import acq400_hapi
import argparse

class RemoteTrigger:
    def __init__(self, uut):
        self.uut = acq400_hapi.Acq400(uut)
    def __call__(self):
        print("{} trigger".format(self.uut.uut))
        self.uut.s0.soft_trigger = 1

def run_shots(args):
    uuts =  [ acq400_hapi.Acq400(u) for u in args.uuts ]

    acq400_hapi.cleanup.init()

    for uut in uuts:
        uut.s1.shot = 0
        if hasattr(uut.s0, 'TIM_CTRL_LOCK'):
            print("LOCKDOWN {}".format(uut))
            uut.s0.TIM_CTRL_LOCK = 1

    shot_controller = acq400_hapi.ShotController(uuts)
    shot = 0

    if args.trigger_uut != None:
        _remote_trigger = RemoteTrigger(args.trigger_uut)
        _soft_trigger = False
    else:
        _remote_trigger = None
        _soft_trigger = True
    try:
        while shot < args.nshots:
            print("shot {} of {}".format(shot, args.nshots))
            shot_controller.run_shot(
                    remote_trigger=_remote_trigger,
                    soft_trigger=_soft_trigger)
            shot += 1
            
    except acq400_hapi.cleanup.ExitCommand:
        print("ExitCommand raised and caught")
    finally:
        print("Finally, going down")

def get_parser():
    parser = argparse.ArgumentParser(description='Shot looptest')
    parser.add_argument('--trigger_uut', default=None, type=str, help="external trigger uut eg ACQ1001+DIO, soft_trigger brought to front panel" )
    parser.add_argument('--nshots', default=9999999, type=int, help="number of shots, default infinit")
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
    run_shots(get_parser().parse_args())




