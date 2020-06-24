#!/usr/bin/env python


import argparse
import json


class uut_handler(argparse.Action):
    def __init__ (self, option_strings, *args, **kwargs):
        super(uut_handler, self).__init__(option_strings=option_strings,
                *args, **kwargs)

    def __call__(self, parser, args, value, option_string=None):
        setattr(args, self.dest, get_uuts(value))


def load_json(json_file):
    with open(json_file) as _json_file:
        json_data = json.load(_json_file)
    return json_data


def get_json_uuts(json_file):

    json = load_json(json_file)
    uut_list = [ uut['name'] for uut in json['AFHBA']['UUT'] ]
    return uut_list


def get_uuts(uuts):
    if uuts[0].startswith("@"):
        uuts = get_json_uuts(uuts[0][1:])
    return uuts


