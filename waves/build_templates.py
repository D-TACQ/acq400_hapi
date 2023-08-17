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

root_prefix = os.getenv("AWG_TEMPLATE_ROOT", "/tmp/AWG")

line = 0
files = []

def process(cmd):
    global line
    global files
    line += 1
    if len(cmd[0]) == 0:
        return -1
    elif cmd[0] == '#':
        return 0

    match = re.search(r'([A-Za-z0-9_-]+)/([0-9]+)', cmd[0])
    if match:
        root = f'{root_prefix}/{match.group(1)}'
        chan = match.group(2)
        cmd = cmd[1:]
        cmd.extend(('--root', root, '--ch', chan))
        print(cmd)
        
    wave_commands = templates.all_templates.get_wave_commands()
    for key in sorted(wave_commands.keys()):
        if cmd[0] == key:
            data, fn = wave_commands[key](cmd[1:])
            files.append((fn, len(data)))
            return 0
        
    print(f'[{line}] ERROR cmd {" ".join(cmd)} cmd not found')
    return 0

def main():
    global files
    
    while process(input(">").split(" ")) >= 0:
        pass

    with open(f'{root_prefix}/MANIFEST', "w") as fp:
        for ii, fnl in enumerate(files):
            fn, fl = fnl
            seg, fn_base = fn[len(root_prefix)+1:].split('/')
            ch, ext = fn_base.split('_')[-1].split('.')
        
            fp.write(f'{ii} {fn} {fl} {seg} {ch} {fn_base}\n')

         

if __name__ == "__main__":
    sys.exit(main())