#!/usr/bin/env python3

"""
A script that streams N samples using streamtonowhered.
"""

import acq400_hapi
import argparse
import time
import datetime
import threading
import os


def update_states(uuts, states):
    for index, uut in enumerate(uuts):
        states[index] = (uut.s0.CONTINUOUS_STATE)
    return states


ST_ARM = 1
ST_RUN = 2

def wait_arm_or_run(uuts, states):
   wait_trigger = True
   while not all(elem == 'CONTINUOUS:STATE ARM' for elem in states):
       states = update_states(uuts, states)
       if all(elem == 'CONTINUOUS:STATE RUN' for elem in states):
           wait_trigger = False
           break
   if wait_trigger:
       return ST_ARM
   else:
       return ST_RUN


def mt_action(uuts, fun, arg):
    threads = []
    for uut in uuts:
        t = threading.Thread(target=fun, args=(uut, arg))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

def init_action(uut, args):
    uut.s0.streamtonowhered = 'stop'
    if args.shot:
        uut.s1.shot = args.shot
    uut.s1.SIG_sample_count_RESET = '1'
    uut.s1.SIG_sample_count_RESET = '0'

def stream_start(uut, args):
    uut.s0.streamtonowhered = 'start'

def stream_stop(uut, args):
    uut.s0.streamtonowhered = 'stop'

def main(args):
    uuts = [ acq400_hapi.Acq400(u) for u in args.uuts ]

    mt_action(uuts, init_action, args)

    states = [ u.s0.CONTINUOUS_STATE for u in uuts ]

    print("Arming systems now - please wait. Do not trigger yet.")

    mt_action(reversed(uuts[1:]), stream_start, args)

    st = wait_arm_or_run(uuts[1:], states[1:])
    if st==ST_ARM:
        pass
    else:
        print("Didn't see wait for trigger, maybe not start at zero")

    uuts[0].s0.streamtonowhered = 'start'

    st = wait_arm_or_run(uuts, states)
    if st==ST_ARM:
        uuts[0].enable_trigger()
        print("All UUTs are armed and ready for trigger.")
    else:
        pass

    # Included as a comment below is an example of how this
    # script was tested. If the user wishes to automate
    # a test that involves this script then a signal generator
    # may be triggered like so:
    # os.system("echo 'TRIG' | nc 10.12.196.174 5025")
    # acq400_hapi.Agilent33210A("10.12.196.174").trigger()

    while not all(elem == 'CONTINUOUS:STATE RUN' for elem in states):
        states = update_states(uuts, states)
        continue

    streamed_samples = 0
    npoll = 0
    time.sleep(1)
    while streamed_samples <= args.samples or npoll < 2:
        print("Streamed {} of {} samples".format(streamed_samples, args.samples))
        streamed_samples = int(uuts[0].s1.sample_count)
        time.sleep(1)
        npoll += 1
        

    print("\nStream finished.")
    mt_action(uuts, stream_stop, args)


def get_parser():
    parser = argparse.ArgumentParser(description='acq400 stream to nowhere')

    parser.add_argument('--shot', default=None, type=int, help="set shot number")
    parser.add_argument('--samples', default=100000, type=int,
    help='The number of samples to stream. Not exact.')

    parser.add_argument('uuts', nargs='+', help="uuts")

    return parser


if __name__ == '__main__':
    main(get_parser().parse_args())


