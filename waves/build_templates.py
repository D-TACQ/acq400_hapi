#!/usr/bin/env python3
# encoding: utf-8
'''
waves.build_templates -- shortdesc

Usage:
    ./waves/build_templates.py CONFIGS/cycloid_scan_templates.txt

'''

import sys
import os
import argparse
import re

from waves.templates.all_templates import get_wave_commands

root_prefix = os.getenv("AWG_TEMPLATE_ROOT", "/tmp/AWG")

class g:
    pass

def process(cmd):
    g.line += 1
    if not cmd or cmd[0] == '#':
        return 0

    match = re.search(r'([A-Za-z0-9_-]+)/([0-9]+)', cmd[0])
    if match:
        root = f'{root_prefix}/{match.group(1)}'
        chan = match.group(2)
        cmd = cmd[1:]
        cmd.extend(('--root', root, '--ch', chan))
        
    wave_commands = get_wave_commands()
    for key in sorted(wave_commands.keys()):
        if cmd[0] == key:
            data, fn = wave_commands[key](cmd[1:])
            if data is not None and fn is not None:
                g.files.append((fn, len(data)))
            return 0
    return 1

def run_main(args):
    init_globals()
    for file in args.files:
        with open(file) as fp:
            for line_num, cmd in enumerate(fp.readlines()):
                if process(cmd.strip().split()) > 0:
                    print(f"Error Line {line_num + 1} invalid: {cmd}")
                    exit(1)
    write_manifest()

def from_array(file_cmds: list):
    init_globals()
    for line_num, cmd in enumerate(file_cmds):
        if process(cmd.strip().split()) > 0:
            return (False, f"Error Line {line_num + 1} invalid: {cmd}")
    write_manifest()
    return (True, 'Finished')

def init_globals():
    g.line = 0
    g.files = []

def write_manifest():
    manifest = f'{root_prefix}/MANIFEST'
    with open(manifest, "w") as fp:
        for ii, fnl in enumerate(g.files):
            fn, fl = fnl
            seg, fn_base = fn[len(root_prefix)+1:].split('/')
            ch, ext = fn_base.split('_')[-1].split('.')
        
            fp.write(f'{ii} {fn} {fl} {seg} {ch} {fn_base}\n')
    print(f'FINISHED {manifest}')

def get_parser():
    parser = argparse.ArgumentParser(description='build_templates')
    parser.add_argument('files', nargs='+', help="files to use")
    return parser

if __name__ == "__main__":
    run_main(get_parser().parse_args())