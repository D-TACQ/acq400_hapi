#!/usr/bin/env python3

"""Remote control to composer webapp

Examples

Load new Template::

    ./user_apps/web/compose_remote.py --file=CONFIGS/cycloid_scan_templates.txt acq1001_434

Compose::

    ./user_apps/web/compose_remote.py --output=oneshot_rearm --nreps=10 --segment=A '5*AA 5*BB' acq1001_434

Load new and compose::

    ./user_apps/web/compose_remote.py  --file=CONFIGS/cycloid_scan_templates.txt --output=oneshot_rearm --nreps=10 --segment=A '5*AA 5*BB' acq1001_434

"""

import argparse
import requests
import json

def run_main(args):
    if not args.port:
        url = f"http://{args.uut}/apps.port"
        error = False
        try:
            r = requests.get(url)
            if r.status_code >= 400:
                error = True
        except Exception as e:
            error = True
        if error:
            exit('[Error] unable to detect api port')
        args.port = int(r.text)
        print(f"Found api on port {args.port}")

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
                'nreps': args.nreps,
                'segment': args.segment,
            }
        }
        send_to_endpoint(url, payload)


def send_to_endpoint(url, payload):
    print(f"\nSending to {url}")
    print('Json: ')
    print(json.dumps(payload, indent=2))
    try:
        r = requests.post(url, json=payload)
        print(f"[{r.status_code}] {r.text}")
    except Exception as e:
        print(f"Error: Unable to post to {url}")

def get_parser():
    parser = argparse.ArgumentParser(description='Remote control to composer webapp')
    parser.add_argument('--port', default=None, help="Set api port")
    parser.add_argument('--file', default=None, help="Template file to upload")
    parser.add_argument('--output', default='oneshot_rearm', help="Composer output options:\
                         oneshot_rearm, oneshot, continuous or a filename")
    parser.add_argument('--nreps', default='', help="Number of pattern repetitions")
    parser.add_argument('--segment', default='A', choices=['A', 'B', 'C', 'D', 'E'], help="Set segment (required)")
    parser.add_argument('pattern', nargs='*', help="Pattern to compose ie 5*AA 5*BB")
    parser.add_argument('uut', help="uut hostname")
    return parser

if __name__ == "__main__":
    run_main(get_parser().parse_args())



