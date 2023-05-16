#!/usr/bin/env python3

import acq400_hapi
import xmltodict
import requests
import re
import paramiko
import json
import argparse
import time
import csv
import os
from getpass import getpass
from acq400_hapi.acq400_print import PR
import datetime


"""
Usage:
    ./test_apps/bolo8_tester.py acq2106_191

    ./test_apps/bolo8_tester.py sites=2,3,4 start_chan=4 end_chan=8 acq2106_191
    ./test_apps/bolo8_tester.py  --url=http://naboo/tests/bolo acq2106_191
    ./test_apps/bolo8_tester.py --cycle=10 --url=http://eigg/home/dt100/bolo_endpoint acq2106_388
    ./test_apps/bolo8_tester.py --sites=1 --cycle=10 --start_chan=1 --end_chan=3 --url=http://eigg/home/dt100/bolo_endpoint/?plot=1 --forever=1 --sleep=7200 acq2106_388

By default will save results to .csv named bolo_result-(serial)-(timestamp).csv in following format
If log_all=1 will save all results to same .csv named bolo_results-(date).csv

    module,channel,I0,Q0,sensitivity,cooling,result
    BE4010064,1,0.0025633,-0.0023786,4.1098,0.046056,PASS
    BE4010064,2,-0.032607,0.026537,4.5616,0.046192,PASS
    BE4010064,3,0.0026337,-0.0022937,4.0439,0.0461,PASS
    BE4010064,4,-0.033375,0.025597,4.4275,0.046204,PASS
    BE4010064,5,0.0023858,-0.0025979,4.085,0.046022,PASS
    BE4010064,6,-0.030446,0.028947,4.6359,0.046279,PASS
    BE4010064,7,0.0025978,-0.0023695,4.0246,0.045802,PASS
    BE4010064,8,-0.032845,0.026247,4.5654,0.046217,PASS

If args.url is set will post json to url with this format:

    {
        "uut_state": {
            "uut_name": "acq2106_388",
            "fpga": "ACQ2106_TOP_64_64_64_64_64_64_9815_9011_32B",
            "fpga_time": "2021/04/14",
            "firmware": "acq400-591-20230424171525",
            "modules": [
                {
                    "model": "BOLO8BLF N=8 M=64",
                    "serial": "BE4010064",
                    "nchan": "24",
                    "full_model": "BOLO8BLF N=8 M=64",
                    "location": "1"
                }
            ],
            "serial": "CE4160388",
            "model": "acq2106sfp",
            "temp": 37.65
        },
        "results": [
            ["1","0.0025633","-0.0023786","4.1098","0.046056","PASS"],
            ["2","-0.032607","0.026537","4.5616","0.046192","PASS"],
            ["3","0.0026337","-0.0022937","4.0439","0.0461","PASS"],
            ["4","-0.033375","0.025597","4.4275","0.046204","PASS"],
            ["5","0.0023858","-0.0025979","4.085","0.046022","PASS"],
            ["6","-0.030446","0.028947","4.6359","0.046279","PASS"],
            ["7","0.0025978","-0.0023695","4.0246","0.045802","PASS"],
            ["8","-0.032845","0.026247","4.5654","0.046217","PASS"],
        ]
    }
"""

def get_parser():
    parser = argparse.ArgumentParser(description='bolo8 auto tester')
    parser.add_argument('--sites', default=None, help="sites to test eg 1,2,3,4,5,6")
    parser.add_argument('--cycles', default=5, type=int, help="number tests on each channel")
    parser.add_argument('--start_chan', default=1, type=int, help="first channel to test per module")
    parser.add_argument('--end_chan', default=8, type=int, help="last channel to test per module")
    parser.add_argument('--url', default=None, help="send results to remote url")
    parser.add_argument('--log_all', default=0, type=int, help="log all results to same csv file")
    parser.add_argument('--forever', default=0, type=int, help="Loop forever on 2 channels must set channels")
    parser.add_argument('--sleep', default=0, type=int, help="sleep after module test use with forever")
    parser.add_argument('--beeper', default="SG0761", help="Sig gen to beep when channel done")
    parser.add_argument('uut_name', help="uut name")
    return parser

class globals:
    uut_state = {}
    temps = []
    fails = 0
    file = None

class Remote_File():
    original_file = None

    ssh = None

    file = None

    def __init__(self, file, params):
        self.file = file
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(**params)
        except Exception as e:
            print(e)
            exit(1)
        cmd = f'cat {file}'
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        self.original_file = stdout.read().decode("utf-8").strip()

    def append(self, line):
        cmd = f"echo '{line}' >> {self.file}"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)

    def reset(self):
        cmd = f"echo $'{self.original_file}' > {self.file}"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)

    def close(self):
        self.ssh.close()
        ssh = None

def run_main(args):
    try:
        globals.uut = acq400_hapi.factory(args.uut_name)
    except Exception as e:
        print(e)
        exit(1)
    globals.uut_state = get_uut_state(globals.uut)

    globals.sites = args.sites.split(',') if args.sites else ['1', '2', '3', '4', '5', '6']
    print(f'Connecting to {args.uut_name}')

    password = getpass()
    params = {
        'hostname': args.uut_name,
        'port': 22,
        'username': 'root',
        'password' : password,
        'timeout': 5
    }
    filename = '/mnt/local/sysconfig/bolo.sh'
    globals.file  = Remote_File(filename, params)

    run_test(args)
    while args.forever:
        run_test(args)

    globals.file.close()
    print('End')

def run_test(args):
    for module in globals.uut_state['modules']:
        if module['location'] not in globals.sites:
            print(f'Skipping site {module["location"]}')
            continue
        print(f'starting test for module: {module["serial"]}')
        results = []
        start_idx = 8 * (int(module['location']) - 1)

        for channel in range(args.start_chan, args.end_chan, 2):
            channel += start_idx
            PR.Yellow(f'Testing channels {channel}-{channel + 1}')

            while not args.forever:
                if args.beeper:
                    beep_beeper(args)

                value = input(f'Is bolometer connected to channels {channel}-{channel + 1} yes / no / stop: ')
                if value == 'yes':
                    break
                if value =='stop':
                    globals.file.reset()
                    globals.file.close()
                    if results:
                        save_module_results(results, module, args)
                    exit('Stopping')
                PR.Yellow(f'Connect bolometer to channels {channel}-{channel + 1}')
                time.sleep(1)

            set_active_channels(globals.file, channel)
            result = test_channels(channel, args)
            results.extend(result)
            globals.file.reset()
            print()

        PR.Green(f'Finished testing {module["serial"]} ')
        PR.Yellow(f'{globals.fails} fails')
        save_module_results(results, module, args)
        if args.sleep:
            print(f"sleeping for {args.sleep}s")
            time.sleep(args.sleep)

def get_temp():
    temps = globals.uut.s0.SYS_TEMP.split(',')
    temps = dict((key, float(value)) for key,value in ((value.split("=") for value in temps)))
    globals.temps.append(temps['mainboard'])
    print(f"Temp is {temps['mainboard']}°C")

def get_uut_state(uut):
    modules = []
    for site_num in uut.s0.sites.split(','):
        part = {}
        site = getattr(uut, f"s{site_num}")
        part['model'] = site.MODEL
        part['serial'] = site.SERIAL
        part['nchan'] = site.NCHAN
        part['full_model'] = site.PART_NUM
        part['location'] = site_num
        modules.append(part)
    fpga = uut.s0.fpga_version.split(' ')
    uut_state = {
        'uut_name'  : uut.s0.HN,
        'fpga'      : fpga[0],
        'fpga_time' : fpga[1],
        'firmware'  : uut.s0.software_version,
        'modules'   : modules,
        'serial'    : uut.s0.SERIAL,
        'model'     : uut.s0.MODEL,
        'temp'      : 0,
    }
    return uut_state

def set_active_channels(file, channel):
    channels = f'{channel} {channel + 1}'
    print(f'Setting active channels to {channels}')
    line = f'export BOLO_ACTIVE_CHAN="{channels}"'
    file.append(line)

def test_channels(channel, args):
    results = []
    for i in range(args.cycles):
        PR.Yellow(f'Test cycle {i + 1}')
        get_temp()
        try:
            run_service()
        except Exception as e:
            print(e)
            response = input('Test Failed exit? y/n ')
            if response == 'y':
                exit()
        values = extract_values(get_xml(args))
        check_for_fails(values)
        results.extend(values)
    return results

def run_service():
    #uut.s14.DSP_RESET = 1
    #time.sleep(0.1)
    #uut.s14.DSP_RESET = 0
    globals.uut.run_service(acq400_hapi.AcqPorts.BOLO8_CAL, eof="END")

def get_xml(args):
    url = f'http://{args.uut_name}/d-tacq/data/BOLO_CAL.xml'
    response = requests.get(url)
    data = xmltodict.parse(response.content)['acqDataXML']['acqData']['v']
    return data

def beep_beeper(args):
    #beeps when its time to change bolometer port
    try:
        acq400_hapi.Agilent33210A(args.beeper).beep(1)
    except Exception as e:
        PR.Red('Beeper not found')

def extract_values(data):
    expr = re.compile('([\d]+)[ ]+([\d\.-]+)[ ]+([\d\.-]+)[ ]+([\d\.-]+)[ ]+([\d\.-]+)[ ]+([\w]+)')
    matches = expr.findall(data)
    return matches

def check_for_fails(values):
    for value in values:
        PR.Yellow(value)
        if value[5] != 'PASS':
            globals.fails += 1
            PR.Red(f"Test failed for channel {value[0]}")

def save_module_results(results, module, args):
    globals.uut_state['temp'] = sum(globals.temps) / len(globals.temps)
    globals.temps = []

    if args.url:
        payload = build_payload(results, module)
        send_to_remote(args.url, payload)

    save_to_file(module, results, args)

def build_payload(results, module):
    state = globals.uut_state.copy()
    state['modules'] = [module]
    payload = {
        'uut_state' : state,
        'results' : results,
    }
    print(json.dumps(payload, indent=4))
    return json.dumps(payload)

def send_to_remote(url, payload):
    print(f'Sending results to {url}')
    r = requests.post(url, payload)
    if r.status_code != 200:
        PR.Red(f'Error: {r.status_code}')
        print(r.text)
        return
    PR.Green('Results received')

def save_to_file(module, results, args):
    filename = f'bolo_result-{module["serial"]}-{round(time.time())}.csv'
    if args.log_all:
        filename = f'bolo_results-{datetime.date.today()}.csv'

    header = ['module', 'channel', 'I0', 'Q0', 'sensitivity', 'cooling', 'result']

    if not os.path.exists(filename):
        with open(filename, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

    with open(filename, 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        results = sorted(results)
        loc_offset = 8 * (int(module['location']) - 1)
        for result in results:
            writer.writerow([module['serial'], int(result[0]) - loc_offset, *result[1:]])

    print(f"saving results to {filename}")

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())
