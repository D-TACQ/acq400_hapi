#!/usr/bin/env python3

import argparse
import requests
import json

"""
Usage:
    ./user_apps/web/compose_remote.py --file cycloid_scan_templatesAABB.txt \
        --output scan_flash.dat --nrep=5 5*AA 5*BB acq1001_590
"""

def run_main(args):
    url = f"http://{args.uut}:{args.port}/endpoint"

    if args.file:
        with open(args.file) as f:
            lines = f.readlines()

        payload = {
            'action' : 'build_template',
            'data': {
                'lines' : lines
            }
        }
        send_to_endpoint(url, payload)

    if args.output and args.pattern:
        payload = {
            'action' : 'awg_compose',
            'data': {
                'output' : args.output,
                'pattern': ' '.join(args.pattern),
                'nrep': args.nrep,
            }
        }
        send_to_endpoint(url, payload)


def send_to_endpoint(url, payload):
    print(f"\nSending to {url}")
    print(json.dumps(payload, indent=2))
    r = requests.post(url, json=payload)
    print(f"[{r.status_code}] {r.text}")

def get_parser():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--port', default=5000, help="endpoint port")
    parser.add_argument('--file', default=None, help="Cmd file to send")
    parser.add_argument('--output', default=None, help="Composer output options:\
                         oneshot_rearm, oneshot, continuous or a filename")
    parser.add_argument('--nrep', default='', help="nrep")
    parser.add_argument('pattern', nargs='*', help="Pattern 5*AA 5*BB")
    parser.add_argument('uut', help="uut hostname")
    return parser

if __name__ == "__main__":
    run_main(get_parser().parse_args())



