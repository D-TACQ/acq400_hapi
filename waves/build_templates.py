#!/usr/bin/env python3
# encoding: utf-8
'''
waves.build_templates -- shortdesc

'''

import sys
import os
import argparse
import re

import templates.all_templates

def process(cmd):
    match = re.search(r'([A-Za-z0-9_-]+)/([0-9]+)', cmd[0])
    if match:
        root = match.group(1)
        chan = match.group(2)
        cmd = cmd[1:]
        cmd.extend(('--root', root, '--ch', chan))
        
    wave_commands = templates.all_templates.get_wave_commands()
    for key in sorted(wave_commands.keys()):
        if cmd[0] == key:
            wave_commands[key](cmd[1:])
            return 0
        
    print(f'cmd {cmd} not found')
    return 0

def main():
     while True:
         process(input(">").split(" "))

if __name__ == "__main__":
    sys.exit(main())