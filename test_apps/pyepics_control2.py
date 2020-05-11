#!/usr/bin/python


import argparse
import epics
import time

# https://en.wikipedia.org/wiki/PID_controller
# u1 = (r1 - y0)*Kp

def control_loop(args, ch):
    print("Starting control loop {}".format(ch))
    uut = args.uut[0]
    pv_Kp = epics.PV("{}:{}:GAIN:{:02d}".format(uut, args.dac, ch))
    pv_r1 = epics.PV("{}:{}:SET:{:02d}".format(uut, args.dac, ch))
    pv_y0 = epics.PV("{}:{}:AI:CH:{:02d}".format(uut, args.adc, ch))
    pv_u1 = epics.PV("{}:{}:AO:SLOW_SET:CH:{:02d}".format(uut, args.dac, ch))

    while True:
        Kp = pv_Kp.get() 
  	r1 = pv_r1.get()
        y0 = pv_y0.get()
        u0 = pv_u1.get()

        u1 = u0 + (r1-y0)*Kp
  
        pv_u1.put(u1)

        time.sleep(0.8) # Wait for the DAC value to change

    return None


def get_args():
    parser = argparse.ArgumentParser(description='PyEPICS control example')

    parser.add_argument('--dac', default=5, type=int, help='AO module site')
    parser.add_argument('--adc', default=1, type=int, help='ADC module site')
    parser.add_argument('--ch', default=1, type=int, help='channel to control')

    parser.add_argument('uut', nargs=1, help="uut")

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    control_loop(args, args.ch)
    return None


if __name__ == '__main__':
    main()
