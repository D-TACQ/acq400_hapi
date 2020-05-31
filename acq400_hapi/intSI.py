#!/usr/bin/env python
import sys
import argparse

class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

DEC = AttributeDict({ 'k': 1000, 'M': 1000000, 'G': 1000000000 })
BIN = AttributeDict({ 'k': 0x400, 'M': 0x100000, 'G': 0x40000000 })

def intSI_cvt(value, decimal=True):
    x = str(value)
    if x == "Inf":
        return sys.maxint

    unit_scale = (DEC if decimal else BIN)
    for k in unit_scale:
        units = x.find(k)
        if units >= 0:
            return int(float(x[:units])* unit_scale[k])
    return int(x)


class intSIAction(argparse.Action):
    def __init__ (self, option_strings, decimal=True, *args, **kwargs):
        super(intSIAction, self).__init__(option_strings=option_strings,
                *args, **kwargs)
        self.decimal = decimal

    def __call__(self, parser, args, value, option_string=None):
       setattr(args, self.dest, intSI_cvt(value, decimal=self.decimal))


# unit test
#[pgm@hoy5 acq400_hapi]$ python acq400_hapi/intSIAction.py -d 20M -b 20M
#Hello args.decval 20000000
#Hello args.binval 20971520

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--decval', action=intSIAction)
    parser.add_argument('-b', '--binval', action=intSIAction, decimal=False)

    args = parser.parse_args()

    print("Hello args.decval {}".format(args.decval))
    print("Hello args.binval {}".format(args.binval))
