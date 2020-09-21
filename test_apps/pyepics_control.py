#!/usr/bin/python


import argparse
import epics
import time


def control_loop(args):
    print("Starting control loop")
    uut = args.uut[0]
    target = args.target

    if args.zero:
        epics.caput("{}:5:AO:SLOW_SET:CH:ALL".format(uut), 0)
        time.sleep(1)  # Wait for the DAC value to change

    adc_val = epics.caget("{}:1:AI:CH:01".format(uut))
    print("target = {}, adc_val = {}".format(target, adc_val))

    # while (target + 0.1) <= adc_val <= (target - 0.1):
    while abs(adc_val - target) > args.tol:
        adc_val = epics.caget("{}:1:AI:CH:01".format(uut))
        new_val = (adc_val + target) / 2
        epics.caput("{}:5:AO:SLOW_SET:CH:ALL".format(uut), new_val)
        print("new_val = {}, adc_val = {}".format(new_val, adc_val))
        time.sleep(0.1)  # Wait for the DAC value to change

    return None


def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')

    parser.add_argument('--target', default=5, type=int,
                        help='Target DAC value.')

    parser.add_argument('--zero', default=1, type=int,
                        help='Whether or not to zero the DAC output to at the start of the loop.')

    parser.add_argument('--tol', default=0.1, type=int,
                        help='Tolerance in the ADC value.')

    parser.add_argument('uut', nargs='+', help="uut")

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    control_loop(args)
    return None


if __name__ == '__main__':
    main()
