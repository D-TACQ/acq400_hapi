#!/usr/bin/python

import argparse
import subprocess


def run_shot(args):
    subprocess.check_call(['mate-terminal', '--window-with-profile=Default', \
            '--title="pgmwashere"',\
           '-e', 'timeout {} top'.format(args.secs)])


def run_main():
    parser = argparse.ArgumentParser(description='run hts all uuts')
    parser.add_argument('--secs', default=100, help='seconds to run')
    parser.add_argument('uut', nargs='+', help='uut')
    run_shot(parser.parse_args())

# execution starts here

if __name__ == '__main__':
    run_main()
