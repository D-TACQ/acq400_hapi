#!/usr/bin/env python3

import argparse
import epics
import time
import datetime
import threading
from acq400_hapi.acq400_print import PR, DISPLAY

"""
Usage:
    ./test_apps/knob_monitor.py --rate_knobs=:0:WR:PPS:COUNT --change_knobs=:0:WR:PPS:FREQ,:0:WR:PPS:ACTIVE \
        acq2206_010 acq2206_009 acq2206_008 acq2206_007 acq2206_006 acq2206_005
"""

class g:
    updates = {}
    changes = {}

def run_main(args):

    epics.ca.poll()
    log('')
    log('Starting Knob monitor')

    for uut in args.uuts:
        for knob in args.rate_knobs:
            knob = f"{uut}{knob}"
            g.updates[knob] = {}
            g.updates[knob]['start_time'] = 0
            g.updates[knob]['updates'] = 0
            g.updates[knob]['rate'] = 0
            g.updates[knob]['errors'] = 0
            g.updates[knob]['duration'] = 0

            thread = threading.Thread(target=rate_monitor, args=(knob, g.updates[knob], args))
            thread.daemon = True
            thread.start()

        for knob in args.change_knobs:
            knob = f"{uut}{knob}"
            g.changes[knob] = {}
            g.changes[knob]['changes'] = 0
            g.changes[knob]['value'] = None
            log(f"START Watching {knob} for changes")
            epics.camonitor(knob, callback=change_callback)

    SCREEN = DISPLAY()
    try:
        while True:
            if g.updates:
                SCREEN.add_line('{REVERSE}Monitoring Rate{RESET}')
                for knob, values in g.updates.items():
                    SCREEN.add(f"{knob} {values['rate']}hz ")
                    duration = round(time.time() - values['start_time'], 2)
                    SCREEN.add(f"{values['updates']} in {duration}s")
                    SCREEN.add(f" {values['errors']} errors")
                    SCREEN.end()
                SCREEN.add_line('')
            if g.changes:
                SCREEN.add_line('{REVERSE}Monitoring Changes{RESET}')
                for knob, values in g.changes.items():
                    SCREEN.add(f"{knob} {values['changes']} changes currently {values['value']}")
                    SCREEN.end()

            SCREEN.render()
                
            time.sleep(1)
    except KeyboardInterrupt:
        SCREEN.render_interrupted()

def rate_monitor(knob, updates, args):
    log(f"START Monitoring update rate for {knob}")
    epics.camonitor(knob, callback=rate_callback)
    count = 0
    updates['start_time'] = time.time()
    last_value = 0
    count = 0
    while True:
        if time.time() >= updates['start_time'] + args.check_rate * count:
            count += 1
            if count == 1:
                continue

            duration = round(time.time() - updates['start_time'], 2)
            current_value = updates['updates'] - last_value
            update_rate = current_value / args.check_rate
            updates['rate'] = round(update_rate, 3)
            if args.target_rate and update_rate != args.target_rate:
                log(f"RATE_ERROR: {knob} @ {update_rate}Hz {updates['updates']} in {duration}s")
                updates['errors'] += 1
            
            last_value = updates['updates']

        time.sleep(0.2)

def rate_callback(pvname=None, **kw):
    if g.updates[pvname]['start_time']:
        g.updates[pvname]['updates'] += 1

def change_callback(pvname=None, char_value=None, **kw):
    g.changes[pvname]['changes'] += 1
    g.changes[pvname]['value'] = char_value
    log(f"CHANGE {pvname} is now {char_value} ")

def log(string):
    timestamp = datetime.datetime.now()
    string = f"[ {timestamp} ] {string}"
    filename = f"knob_monitor.log"
    with open(filename, 'a') as file:
        file.write(string)
        file.write('\n')

def comma_list(string):
    return string.split(',')

def get_parser():
    parser = argparse.ArgumentParser(description='knob monitor')
    parser.add_argument('--rate_knobs', default=[], type=comma_list, help='knobs to monitor update rate')
    parser.add_argument('--target_rate', default=1, type=int, help='write to log if rate is not target rate')
    parser.add_argument('--check_rate', default=60, type=int, help='How often to check target rate') 
    parser.add_argument('--change_knobs', default=[], type=comma_list, help='knobs to monitor for changes')
    parser.add_argument('uuts', nargs='+', help="uuts")
    return parser

if __name__ == '__main__':
	run_main(get_parser().parse_args())