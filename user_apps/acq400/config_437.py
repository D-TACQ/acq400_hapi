"""
A python script to set gains on an acq437.
"""


import argparse
import acq400_hapi


def set_params(args):
    # Set gain range and sample rate for the acq437 only if the user has specified the parameters.

    uuts = [acq400_hapi.Acq400(u) for u in args.uuts]

    for uut in uuts:

        if args.gain != "0":
            uut.s1.GAIN_ALL = args.gain

        if args.sample_rate != "0":
            uut.s1.ACQ43X_SAMPLE_RATE = args.sample_rate

    return None


def run_main():
    parser = argparse.ArgumentParser(description='acq400 set gains')

    parser.add_argument('--gain', default="0", type=str,
                        help="Gain range to set on the device. Options: X1, X10, X100, X1000")
    parser.add_argument('--sample_rate', default="0", type=str,
                        help="Set sample rate on 437 device.")

    parser.add_argument('uuts', nargs='+', help="uuts")
    args = parser.parse_args()
    set_params(args)


if __name__ == '__main__':
    run_main()
