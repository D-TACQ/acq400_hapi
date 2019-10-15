#!/usr/bin/env python


"""
This is a regression test suite that uses a function generator and the onboard
GPG to test UUTs. For more information on regression tests please refer to the
D-TACQ wiki page:

http://eigg-fs:8090/mediawiki/index.php/Products:ACQ400:Regression_Testing

Usage:

python regression-test-suite.py --trg=int --test=post --channels="1,1" UUT1 UUT2

python regression-test-suite.py --trg=ext --test=post --channels="1,1" UUT1 UUT2



"""

from __future__ import print_function
import acq400_hapi
import numpy as np
import os
import time
import argparse
import socket
from future import builtins
import matplotlib.pyplot as plt


def create_fig(args, test):
    if test == "post":
        fig, axs = plt.subplots(3, 1, sharey=True, gridspec_kw={'hspace': 0.9})
    else:
        fig, axs = plt.subplots(6, 1, sharey=True, gridspec_kw={'hspace': 0.9})
    return fig, axs


def create_rtm_stl():
    stl =  "0,f\n \
    10000,0\n \
    20000,f\n \
    30000,0\n \
    40000,f\n \
    50000,0\n \
    60000,f\n \
    70000,0\n \
    80000,f\n \
    90000,0\n \
    100000,f\n \
    110000,0\n \
    120000,f\n \
    130000,0\n \
    140000,f\n \
    150000,0\n \
    160000,f\n \
    170000,0\n \
    180000,f\n \
    190000,0\n \
    200000,f\n \
    210000,0\n \
    220000,f\n \
    230000,0\n \
    240000,f\n \
    250000,0\n \
    260000,f\n \
    270000,0\n \
    280000,f\n \
    290000,0"
    return stl


def create_rgm_stl():
    # An example STL file for regression test purposes.
    stl = "0,f\n \
    5000,0\n \
    20000,f\n \
    35000,0\n \
    40000,f\n \
    45000,0\n \
    60000,f\n \
    75000,0\n \
    80000,f\n \
    200000,0"
    return stl


def calculate_frequency(args, uut, divisor):
    # calculate a reasonable frequency from the clock speed of the master uut.
    clk_freq = (int(float(uut.s0.SIG_CLK_S1_FREQ.split(" ")[1])))
    print("\n\nSample Rate = ",clk_freq,"\n\n")
    freq = clk_freq / divisor
    if int(freq) == 0 :
        print("\n\nWarning CLK Frequency reading ZERO!!!\n\n")
        exit()
    return freq


def trigger_system(args, sig_gen):
    # if "rtm" not in args.test:
    time.sleep(1)
    if args.test != "rtm":
        print("Triggering now.")
        sig_gen.send("TRIG\n".encode())
        if args.trg[1] == 0 and args.test == "pre_post":
            time.sleep(2)
            sig_gen.send("TRIG\n".encode())
    return None


def config_gpg(uut, args, trg=1):
    # The following settings are very test specific and so they
    # have not been included in a library function.
    uut.s0.gpg_enable = 0
    uut.s0.gpg_clk = "1,2,1" # GPG clock is the same as the site.
    uut.s0.gpg_trg = "1,{},1".format(trg)
    uut.s0.gpg_mode = 3 # LOOPWAIT

    if args.test == "rgm":
        stl = create_rgm_stl()
    else:
        stl = create_rtm_stl()
    try:
        uut.load_gpg(stl)
    except Exception:
        print("Load GPG has failed. If you want to use the GPG please make sure")
        print("that the GPG package has been enabled.")
        return False
    uut.s0.gpg_enable = 1
    return True


def configure_sig_gen(sig_gen, args, freq):
    print("Configuring sig gen.")

    sig_gen.send("VOLT 1\n".encode())
    sig_gen.send("OUTP:SYNC ON\n".encode())
    freq_string = "FREQ {}\n".format(freq)
    sig_gen.send(freq_string.encode())
    sig_gen.send("FUNC:SHAP SIN\n".encode())

    if args.test == "post":
        if args.trg[1] == 0:
            sig_gen.send("BURS:STAT ON\n".encode())
            sig_gen.send("BURS:NCYC 1\n".encode())
            sig_gen.send("TRIG:SOUR BUS\n".encode())
        elif args.trg[1] == 1:
            sig_gen.send("BURS:STAT OFF\n".encode())
            sig_gen.send("TRIG:SOUR IMM\n".encode())

        if args.trg[2] == 0:
            # If ext falling then we need two sine waves
            print("TRG FALLING set sg")
            sig_gen.send("BURS:STAT ON\n".encode())
            sig_gen.send("BURS:NCYC 3\n".encode())


    if args.test == "pre_post":
        sig_gen.send("BURS:STAT ON\n".encode())
        sig_gen.send("BURS:NCYC 1\n".encode())
        sig_gen.send("TRIG:SOUR BUS\n".encode())

    elif args.test == "rtm" or args.test == "rgm":
        # sig_gen.send("FREQ 1000\n".encode())
        sig_gen.send("TRIG:SOUR IMM\n".encode())
        sig_gen.send("BURS:STAT OFF\n".encode())
        if args.test == "rgm":
            sig_gen.send("BURS:STAT ON\n".encode())
            sig_gen.send("BURS:NCYC 5\n".encode())
            sig_gen.send("TRIG:SOUR BUS\n".encode())
    elif args.test == "rtm_gpg":
        sig_gen.send("TRIG:SOUR IMM\n".encode())
        sig_gen.send("BURS:STAT OFF\n".encode())
        sig_gen.send("FUNC:SHAP RAMP\n".encode())
        sig_gen.send("FREQ 1\n".encode())
    return None


def check_master_slave(args, uut):
    print(uut.s0.HN, uut.s0.sync_role)
    return None


def check_es(events):
    success_flag = True
    for uut_es in events:
        if uut_es == events[0]:
            continue
        else:
            print("\nES comparison FAILED!\n")
            success_flag = False
            return False
    if success_flag == True:
        print("\nES Comparison successful!\n")
    return True


def show_es(events, uuts):
    uut_list = list(range(0, len(uuts)))
    lines = [events[counter][1].splitlines() for counter in uut_list]
    for l in zip(*lines):
        print(*l, sep='')
    for event in events:
        print("{}\n".format(event[0])) # Print indices too!
    return None


def save_data(uuts):
    for uut in uuts:
        data = uut.read_muxed_data()
        data[0].tofile("{}_shot_data".format(uut.s0.HN))
    return None


def verify_inputs(args):
    tests = ["post","pre_post", "rtm", "rtm_gpg", "rgm"]
    if args.test not in tests:
        print("Please choose from one of the following tests:")
        print(tests)
        exit(1)
    return None


def custom_test(args, uuts):
    return None


def run_test(args, axs, plt_count):
    CRED = "\x1b[1;31m"
    CGREEN = "\x1b[1;32m"
    CYELLOW = "\x1b[1;33m"
    CEND = "\33[0m"

    # plt.figure() # Open a new figure for each test (only in all tests mode).

    # fig, axs = plt.subplots(1, 6, sharey=True)
    uuts = []
    success_flag = True
    channels = eval(args.channels[0])
    verify_inputs(args)

    for uut in args.uuts:
        uut = acq400_hapi.Acq400(uut)
        uut.s0.set_abort
        uut.s0.transient = "DEMUX={}".format(args.demux)
        # check_master_slave(args, uut)
        uut.s0.transient # print transient config
        uuts.append(uut)

    if args.config_sig_gen == 1:
        sig_gen = socket.socket()
        sig_gen.connect((args.sig_gen_name, 5025))
        freq = calculate_frequency(args, uuts[0], args.clock_divisor)
        configure_sig_gen(sig_gen, args, freq)

    for iteration in list(range(1, args.loops+1)):
        data = []
        events = []
        # plt.clf()
        print("event DEBUG: ", args.event)
        for index, uut in reversed(list(enumerate(uuts))):

            if args.test == "pre_post":
                if index == 0:
                    uut.configure_pre_post("master", trigger=args.trg, event=args.event)
                else:
                    # uut.s0.sync_role = "slave"
                    uut.configure_pre_post("slave")

            elif args.test == "post":
                if index == 0:
                    uut.configure_post("master", trigger=args.trg)
                else:
                    uut.configure_post("slave", trigger=args.trg)

            elif args.test == "rtm":
                if index == 0:
                    uut.configure_rtm("master", trigger=args.trg, event=args.event)
                else:
                    uut.configure_rtm("slave")

            elif args.test == "rtm_gpg":
                if index == 0:
                    uut.configure_rtm("master", trigger=args.trg, gpg=1, event=args.event)
                    gpg_config_success = config_gpg(uut, args, trg=0)
                    if gpg_config_success != True:
                        print("Breaking out of test {} now.".format(args.test))
                        break
                else:
                    uut.configure_rtm("slave")

            elif args.test == "rgm":
                if index == 0:
                    uut.configure_rgm("master", trigger=args.trg, post=75000, gpg=1)
                    gpg_config_success = config_gpg(uut, args, trg=0)
                    if gpg_config_success != True:
                        print("Breaking out of test {} now.".format(args.test))
                        break
                else:
                    uut.s0.sync_role = "slave"
                    uut.configure_rgm("slave", post=75000)

            uut.s0.set_arm
            uut.statmon.wait_armed()

        try:
            # Here the value of gpg_config_success is verified, as we need to
            # break out of the outer loop if it is false. If it does not exist
            # then do nothing.
            if gpg_config_success != True:
                break
        except NameError:
            print("")

        time.sleep(5)

        trigger_system(args, sig_gen)

        for index, uut in enumerate(uuts):
            uut.statmon.wait_stopped()
            if args.demux == 1:
                data.append(uut.read_channels(tuple(channels[index])))
            else:
                data.append(uut.read_channels((0), -1))
            events.append(uut.get_es_indices(human_readable=1, return_hex_string=1))

        if args.demux == 0:
            success_flag = check_es(events)
            if args.show_es == 1:
                show_es(events, uuts)
            save_data(uuts)
            for index, data_set in enumerate(data):
                for ch in channels[index]:
                    axs[plt_count].plot(data_set[0][ch-1::uuts[index].nchan()])

        else:
            for data_set in data:
                for ch in data_set:
                    # plt.plot(ch)
                    axs[plt_count].plot(ch)
        axs[plt_count].grid(True)
        axs[plt_count].set_title("Test: {} Runs: {} Trg: {} Event: {}".format(args.test, args.loops, args.trg, args.event))
        # plt.pause(0.001)
        # plt.show(block=False)

        if args.custom_test == 1:
            custom_test(args, uuts)

        if success_flag == False:
            print(CRED , "Event samples are not identical. Exiting now. " , CEND)
            print("Tests run: ", iteration)
            plt.show()
            exit(1)
        else:
            print(CGREEN + "Test successful. Test number: ", iteration, CEND)
        # import code
        # code.interact(local=locals())
    print("Finished '{}' test. Total tests run: {}".format(args.test, args.loops))
    # plt.pause(0.001)
    # plt.show(block=False)
    # plt.show()
    return axs[plt_count]


def run_main():
    parser = argparse.ArgumentParser(description='acq400 regression test.')

    parser.add_argument('--test', default="pre_post", type=str,
    help='Which test to run. Options are: all, post, pre_post, rtm, rtm_gpg, rgm. \
    Default is pre_post. The "all" option can be used to test every test mode \
    with every trigger mode.')

    parser.add_argument('--trg', default="1,0,1", type=str,
    help='Which trigger to use. Default is 1,0,1. User can also specify \
    --trg=all so that the chosen test will be run multiple times with all \
    trigger types.')

    parser.add_argument('--event', default="1,0,1", type=str,
    help='Which event to use. Default is 1,0,1. User can also specify \
    --event=all so that the chosen test will be run multiple times with all \
    event types.')

    parser.add_argument('--config_sig_gen', default=1, type=int,
    help='If True, configure signal generator. Default is 1 (True).')

    parser.add_argument('--sig_gen_name', default="A-33600-00001", type=str,
    help='Name of signal generator. Default is A-33600-00001.')

    parser.add_argument('--channels', default=['[1],[1]'], nargs='+',
    help='One list per UUT: --channels=[[1],[1]] plots channel 1 on UUT1 and 2')

    parser.add_argument('--clock_divisor', default=20000, type=int,
    help="The speed at which to run the sig gen. 20,000 is human readable and \
    is default.")

    parser.add_argument('--demux', default=1, type=int,
    help="Whether or not to have demux configured on the UUT. Default is 1 \
    (True)")

    parser.add_argument('--show_es', default=1, type=int,
    help="Whether or not to show the event samples when demux = 0. Default is 1\
    (True)")

    parser.add_argument('--loops', default=1, type=int,
    help="Number of iterations to run the test for. Default is 1.")

    parser.add_argument('--custom_test', default=0, type=int,
    help="This argument allows the user to write a custom test in the custom \
    test function. Default is disabled (0).")

    parser.add_argument('uuts', nargs='+', help="Names of uuts to test.")

    args = parser.parse_args()
    all_tests = ["post", "pre_post", "rtm", "rtm_gpg", "rgm"]

    all_trgs = [[1,0,0], [1,0,1], [1,1,1]]
    all_events = [[1,0,0], [1,0,1]] # Not interested in any soft events.

    if args.test.lower() == "all":
        print("You have selected to run all tests.")
        print("Now running each test {} times with ALL triggers " \
                                "and ALL events.".format(args.loops))

        for test in all_tests:
            args.test = test
            fig, axs = create_fig(args, test)
            # fig, axs = plt.subplots(1, 6, sharey=True)
            plt_count = -1

            for trg in all_trgs:
                args.trg = trg

                if test == "post": # Don't need any events for post mode.
                    args.event = "N/A"
                    print("\nNow running: {} test with" \
                                        " trigger: {}\n".format(test, args.trg))
                    plt_count += 1
                    run_test(args, axs, plt_count)
                else:

                    for event in all_events:
                        args.event = event
                        print("\nNow running: {} test with trigger: {} and" \
                        " event: {}\n".format(test, args.trg, args.event))
                        plt_count += 1
                        run_test(args, axs, plt_count)
            plt.show()

    elif args.trg == "all" and args.event == "all":
        fig, axs = create_fig(args, args.test)
        plt_count = -1
        
        for trg in all_trgs:
            args.trg = trg
            if args.test == "post": # Don't need any events for post mode.
                args.event = "N/A"
                print("\nNow running: {} test with" \
                                    " trigger: {}\n".format(args.test, args.trg))
                plt_count += 1
                run_test(args, axs, plt_count)
            else:
                for event in all_events:
                    args.event = event
                    print("\nNow running: {} test with trigger: {} and" \
                    " event: {}\n".format(args.test, args.trg, args.event))
                    plt_count += 1
                    run_test(args, axs, plt_count)
        plt.show()

    elif args.trg == "all":
        fig, axs = create_fig(args, args.test)
        plt_count = -1
        for trg in all_trgs:
            args.trg = trg
            plt_count += 1
            run_test(args, axs, plt_count)
        plt.show()

    elif args.event == "all":
        args.trg = args.trg.split(",")
        args.trg = [int(i) for i in args.trg]
        print("Hello world!")
        fig, axs = create_fig(args, args.test)
        plt_count = -1
        for event in all_events:
            args.event = event
            plt_count += 1
            run_test(args, axs, plt_count)
        plt.show()

    else:
        test = args.test
        fig, axs = create_fig(args, test)
        args.trg = args.trg.split(",")
        args.trg = [int(i) for i in args.trg]
        args.event = args.event.split(",")
        args.event = [int(i) for i in args.event]
        plt_count = -1
        plt_count += 1
        run_test(args, axs, plt_count)
    plt.show()


if __name__ == '__main__':
    run_main()
