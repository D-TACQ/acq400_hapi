#!/usr/bin/env python

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

##script will post results to remote server as json in this format
##FORMAT:
#{
#   "uut_state": {
#      "uut_name": "acq2106_191",
#      "fpga": "ACQ2106_TOP_64_64_64_64_64_64_9815_9011_32B",
#      "fpga_date": "2021/04/14",
#      "firmware": "acq400-571-20230315162732",
#      "modules": [
#         {
#         "model": "BOLO8BLF",
#         "serial": "BE4010056",
#         "nchan": "24",
#         "full_model": "BOLO8BLF N=8 M=64",
#         "location": "1"
#         }
#      ],
#      "serial": "CE4160191",
#      "model": "acq2106sfp"
#    },
#   "results": [
#      ["1", "0.0018474", "-0.0021859", "1.1501", "0.046952", "PASS"],
#      ["2", "-0.005299", "0.0057945", "1.1716", "0.04682", "PASS"]
#   ]
#}


#usage
#./user_apps/special/bolo8_logger.py acq2106_191
#./user_apps/special/bolo8_logger.py sites=2,3,4 start_chan=4 end_chan=8 acq2106_191
#./user_apps/special/bolo8_logger.py --url=http://naboo/tests/bolo acq2106_191



def get_parser():
    parser = argparse.ArgumentParser(description='bolo8 auto tester')
    parser.add_argument('--sites', default=None, help="sites to test eg 1,2,3,4,5,6")
    parser.add_argument('--cycles', default=5, type=int, help="number tests on each channel")
    parser.add_argument('--start_chan', default=1, type=int, help="first channel to test per module")
    parser.add_argument('--end_chan', default=8, type=int, help="last channel to test per module")
    parser.add_argument('--url', default=None, help="send results to remote url")
    parser.add_argument('--log_all', default=0, type=int, help="log all results to same csb file")
    parser.add_argument('uut_name', help="uut name")
    return parser

class globals:
    uut_state = {}

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
    test_loop(args)

def test_loop(args):
    try:
        uut = acq400_hapi.factory(args.uut_name)
    except Exception as e:
        print(e)
        exit(1)
    globals.uut_state = get_uut_state(uut)

    selected_sites = args.sites.split(',') if args.sites else ['1', '2', '3', '4', '5', '6']
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
    file = Remote_File(filename, params)

    for module in globals.uut_state['modules']:
        if module['location'] not in selected_sites:
            print(f'Skipping site {module["location"]}')
            continue
        print(f'starting test for module: {module["serial"]}')
        results = []
        start_idx = 8 * (int(module['location']) - 1)

        for channel in range(args.start_chan, args.end_chan, 2):
            channel += start_idx
            PR.Yellow(f'Testing channels {channel}-{channel + 1}')

            while True:
                value = input(f'Is bolometer connected to channels {channel}-{channel + 1} yes / no / stop: ')
                if value == 'yes':
                    break
                if value =='stop':
                    file.reset()
                    file.close()
                    if results:
                        save_module_results(results, module, args)
                    exit('Stopping')
                PR.Yellow(f'Connect bolometer to channels {channel}-{channel + 1}')
                time.sleep(1)

            set_active_channels(file, channel)
            result = test_channels(uut, channel, args)
            results.extend(result)
            file.reset()
            print()

        PR.Green(f'Finished testing {module["serial"]} ')
        save_module_results(results, module, args)

    file.close()
    print('End')

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
    }
    return uut_state

def set_active_channels(file, channel):
    channels = f'{channel} {channel + 1}'
    print(f'Setting active channels to {channels}')
    line = f'export BOLO_ACTIVE_CHAN="{channels}"'
    file.append(line)

def test_channels(uut, channel, args):
    results = []
    for i in range(args.cycles):
        PR.Yellow(f'Test cycle {i + 1}')
        try:
            run_service(uut)
        except:
            response = input('Test Failed try again? y/n')
            if response != 'y':
                exit()
            run_service(uut)
        results.extend(extract_values(get_xml(args)))
    return results

def run_service(uut):
    uut.s14.DSP_RESET = 1
    time.sleep(0.1)
    uut.s14.DSP_RESET = 0
    uut.run_service(acq400_hapi.AcqPorts.BOLO8_CAL, eof="END")

def get_xml(args):
    url = f'http://{args.uut_name}/d-tacq/data/BOLO_CAL.xml'
    response = requests.get(url)
    data = xmltodict.parse(response.content)['acqDataXML']['acqData']['v']
    return data

def extract_values(data):
    expr = re.compile('([\d]+)[ ]+([\d\.-]+)[ ]+([\d\.-]+)[ ]+([\d\.-]+)[ ]+([\d\.-]+)[ ]+([\w]+)')
    matches = expr.findall(data)
    for match in matches:
        PR.Yellow(match)
    return matches

def save_module_results(results, module, args):

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
        for result in results:
            writer.writerow([module['serial'], *result])

    print(f"saving results to {filename}")

# execution starts here

if __name__ == '__main__':
    run_main(get_parser().parse_args())
