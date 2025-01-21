#!/usr/bin/env python3

""" Capture loop Test

    Run a transient then offload the data

    pre-requisite: UUT's are configured and ready to make a transient capture 
    eg clk is running. soft trg enabled
    eg transient length set.
"""

import argparse
import acq400_hapi


def run_main(args):
    uut = acq400_hapi.factory(args.uut) # init connection to uut

    uut.s0.set_abort = 1 #ensure uut is idle

    uut.s0.transient = f"PRE=0 POST={args.post} SOFT_TRIGGER={args.soft_trigger} DEMUX=0" # set the transient shot parameters

    shot_controller = acq400_hapi.ShotController(uut) # init ShotController
    try:
        
        while True:
            shot = int(uut.s1.shot) + 1
            print(f"SHOT {shot}")

            shot_controller.run_shot(soft_trigger=args.soft_trigger) #run shot

            data = uut.read_channels() # read data as channels

            if args.save:
                filename = f"{uut.uut}.SHOT{shot}.dat"
                data.T.tofile(filename) #save data as samples
                print(f"Data saved to {filename}")
            
            if args.wait: input('Enter to Continue.')


    except KeyboardInterrupt:
        pass

    print('Done')

def get_parser():
    parser = argparse.ArgumentParser(description="Capture loop Test")
    parser.add_argument('--soft_trigger', default=1, type=int, help="Use a soft (internal) Trigger")
    parser.add_argument('--post', default=100000, type=int, help="Post samples")
    parser.add_argument('--save', default=0, type=int, help="Save shot data to disk")
    parser.add_argument('--wait', default=0, type=int, help="Wait for user input before next shot")

    parser.add_argument('uut', help="uut name")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())





