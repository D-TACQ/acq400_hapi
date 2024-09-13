#!/usr/bin/env python3

import os
import datetime
import time
import requests
import argparse
import requests
import csv
import numpy as np
from matplotlib import pyplot as plt
import acq400_hapi
from acq400_hapi import PR
import json

"""
Usage:
    Calibration Test :
    ./test_apps/bolo8_tester.py acq2106_123 --chans=all 

    Cal and cap then plot and save results:
    ./test_apps/bolo8_tester.py acq2106_123 --chans=all --cycles=5 --plot=1 --save=1 --cal=1 --cap=1
"""

def get_parser():
    parser = argparse.ArgumentParser(description='bolo8 tester')
    parser.add_argument('--cal', default=1, type=int, help="Run calibrate")
    parser.add_argument('--cap', default=0, type=int, help="Run capture")
    parser.add_argument('--chans', default='1,2', help="Channels to test eg 1,2,10-15 or all")
    parser.add_argument('--cycles', default=1, type=int, help="Number of tests per channel")
    parser.add_argument('--foils', '--bolo_chans', default=2, type=int, help="Available bolometer foils")
    parser.add_argument('--bolo', '--bolo_id', default='IPT008', help="Bolometer serial")
    parser.add_argument('--beeper', default="SG0106", help="siggen to beep when ready")
    parser.add_argument('--plot', default=1, type=int, help="0 no plot, 1 plot final results, 2 plot every capture")
    parser.add_argument('--tocsv', default=1, type=int, help="save calibration results to csv")
    parser.add_argument('--save', default=0, type=int, help="save channel capture data to file")
    parser.add_argument('--url', default=None, help="remote url to send results json and chandata")
    parser.add_argument('--dtypes', default='PWR', type=type_list, help="data types to plot and save ie PWR,MAG,PHI")
    parser.add_argument('--ptotal', default=40000, type=int, help="Plot total samples")
    parser.add_argument('--strobe', default=0, type=int, help="Strobe led (enabled: 1) or (disabled: 0)")
    parser.add_argument('uutname', help="uut name")
    return parser

def type_list(value):
    value = value.upper()
    return value.split(',')

DEFAULT_STL = [
    "# sos, normalized, delta coding, minimize number of states",
    "# CSCALE=6250 to run at 100ms tick",
    "0,0",
    "+48,0",
    "+16,2",
    "+16,0",
    "+16,2",
    "+16,0",
    "+16,2",
    "+16,0",
    "+48,2",
    "+48,0",
    "+16,2",
    "+48,0",
    "+16,2",
    "+48,0",
    "+48,0",
    "+16,2",
    "+16,0",
    "+16,2",
    "+16,0",
    "+16,2",
    "+16,0",
    "+96,0",
]
class bolo_handler:

    def __init__(self, args):
        PR.Reverse(f"Testing {args.uutname} with bolo {args.bolo}")
        self.args = args
        self.cycle = 0
        self.uut = acq400_hapi.factory(args.uutname)

        self.get_channels()
        self.build_chanset()

        self.strobe = self.StrobeHelper(self.uut)
        self.results = self.ResultHelper()

        self.timestamp = datetime.datetime.today().strftime('%Y.%b.%d.%H.%M')

        self.data = {}
        self.calibration = {}
        self.dat_file = None
        self.beeper = None

        self.active_types = set()
        self.data_types = {
            'PWR': {
                'nidx' : 0,
                'unit': 'mW',
                'scaler' : 1.25 * 3.64e-6 * 1000
            },
            'PHI': {
                'nidx' : 1,
                'unit': 'codes',
                'scaler' : 1
            },
            'MAG': {
                'nidx' : 2,
                'unit': 'mV',
                'scaler' : 1.25 * 5.688e-8 * 1000
            }
        }

    #handler funcs
    
    def get_channels(self):
        self.channels = []
        if self.args.chans.upper() == 'ALL':
            self.channels = list(range(1, int(self.uut.nchan() / 3 + 1)))
            return
        for chan in self.args.chans.split(','):
            if '-' in chan:
                chan = list(map(int, chan.split('-')))
                self.channels.extend(list(range(chan[0], chan[1] + 1)))
                continue
            self.channels.append(int(chan))

    def build_chanset(self):
        channels = self.channels.copy()
        self.chanset = []
        new_set=[channels.pop(0)]
        for chan in channels:
            if chan - new_set[0] < self.args.foils:
                new_set.append(chan)
                continue
            self.chanset.append(new_set)
            new_set = [chan]
        self.chanset.append(new_set)
    
    def set_cycle(self, cycle):
        self.cycle = cycle
        print()
        print(f"Cycle {self.cycle}/{self.args.cycles}")

    def set_active(self, chanset):
        self.active_chans = chanset
        self.chan_str = ','.join(map(str, self.active_chans))
        self.uut.s14.BOLO_ACTIVE_CHAN = self.chan_str
        print(f"Setting active chan to {self.chan_str}")
    
    def ask_if_connected(self):
        self.beep_beeper(1)
        while True:
            ans = input(f"Is bolometer ({self.args.bolo}) connected to channels {self.chan_str}? [yes, quit]: ")
            if ans.lower().startswith('y'):
                break
            if ans.lower().startswith('q'):
                raise KeyboardInterrupt
            print('Invalid input')

    def beep_beeper(self, count=2, intvl=0.3):
        try:
            if self.beeper == None or self.beeper == -1:
                self.beeper = acq400_hapi.Agilent33210A(self.args.beeper)
            for i in range(count):
                time.sleep(intvl)
                self.beeper.send("SYST:BEEP")
        except:
            if self.beeper != -1:
                PR.Red('Beeper not found')
            self.beeper = -1

    ##cal funcs

    def run_cal(self):
        print()
        PR.Reverse(f" Running calibration on channels {self.chan_str} ")
        self.uut.s1.trg = "1,1,1" # Set soft trigger for calibration.
        self.uut.run_service(acq400_hapi.AcqPorts.BOLO8_CAL, eof="END")
        self.get_remote_cal()
        self.print_cal(self.active_chans, False)

    def get_remote_cal(self):
        url = f"http://{self.uut.uut}/tmp/calibfit.log"
        response = requests.get(url)
        if response.status_code != 200:
            exit(f"Error getting calibration")
        for cal in response.text.split('\n'):
            if not cal:
                continue
            self.log_cal(cal)
        
    def log_cal(self, cal):
        columns = ['channel', 'sensitivity', 'cooling', 'I0', 'Q0']
        chan = 0
        for idx, value in enumerate(cal.split()):
            if idx == 0:
                chan = int(value)
                if chan not in self.calibration:
                    self.calibration[chan] = {}
                continue
            column = columns[idx]
            if column not in self.calibration[chan]:
                self.calibration[chan][column] = []
            self.calibration[chan][column].append(float(value))

    def check_calibration(self):
        SENS_MIN, SENS_MAX = (1, 15)
        COOL_MIN, COOL_MAX = (0, 1)
        testname = 'calibration'
        self.results.register(testname)
        for chan in self.calibration:
            inrange = True

            sens = self.calibration[chan]['sensitivity']
            cool = self.calibration[chan]['cooling']

            if min(sens) < SENS_MIN or max(sens) > SENS_MAX:
                inrange = False
            if min(cool) < COOL_MIN or max(cool) > COOL_MAX:
                inrange = False

            if inrange:
                self.results.passed(chan)
                self.calibration[chan]['status'] = 'Pass'
                #PR.Green(f"Pass: CH{chan} calibration in range")
                continue
            self.results.failed(chan)
            self.calibration[chan]['status'] = 'Fail'
            PR.Red(f"Fail: CH{chan} calibration outside range")

    def print_cal(self, chans=None, average=True):
        print()
        PR.Reverse(f" Calibration results {'(averaged)' if average else ''}: ")
        for chan, cal in self.calibration.items():
            if chans and chan not in chans:
                continue
            status = cal['status'] if 'status' in cal else ''
            if average:
                sens = round(sum(cal['sensitivity']) / len(cal['sensitivity']), 5)
                cool = round(sum(cal['cooling']) / len(cal['cooling']), 5)
            else:
                sens = cal['sensitivity'][-1]
                cool = cal['cooling'][-1]
            print(f"Chan {chan} \t Sensitivity {sens} \t Cooling {cool} \t {status}")

    def cal_to_csv(self):
        filepath = self.gen_filepath('csv')
        print(f"Saving calibration to {filepath}")
        with open(filepath, 'w') as f:
            w = csv.writer(f)
            w.writerow(['channel', 'sensitivity', 'cooling', 'I0', 'Q0', 'status'])
            for chan, cal in self.calibration.items():
                sens = None
                for ii, values in enumerate(cal['sensitivity']):
                    w.writerow([
                        chan, 
                        cal['sensitivity'][ii],
                        cal['cooling'][ii],
                        cal['I0'][ii],
                        cal['Q0'][ii],
                        cal['status']
                    ])

    #cap funcs
    def run_cap(self):
        print()
        PR.Reverse(f" Running capture on channels {self.chan_str} ")
        self.uut.s0.transient = "POST=100000 SOFT_TRIGGER=0 DEMUX=0"
        
        if self.args.strobe: self.strobe.start()
        time.sleep(1)
        self.uut.s0.set_arm = '1'
        print('Arming')

        self.uut.statmon.wait_armed()
        self.uut.s0.soft_trigger = '1'
        print('Triggering')

        self.uut.statmon.wait_stopped()
        if self.args.strobe: self.strobe.stop()
        print('Stopped')


        if self.args.plot > 0 or self.args.save > 1:
            for type in self.args.dtypes:
                self.get_data(type)

        self.check_PWR_sync()

        if self.args.plot > 1:
            self.plot_data(self.active_chans, 1)

        self.dsp_reset()

    def dsp_reset(self):
        self.uut.s14.DSP_RESET = 1
        time.sleep(0.1)
        self.uut.s14.DSP_RESET = 0

    def get_data(self, type):
        if type not in self.data_types:
            PR.Red(f"data type {type} is invalid")
            return
        self.active_types.add(type)
        
        dtype = self.data_types[type]
        for chan in self.active_chans:
            raw = self.uut.read_channels(chan * 3 - dtype['nidx'])[-1]
            if chan not in self.data:
                self.data[chan] = {}
            self.data[chan][type] = raw.reshape(1,-1)[0]

    def save_data(self):
        out = []
        total_chans = 0
        types = sorted(list(self.active_types))
        for chan in self.data:
            for type in types:
                dat = self.data[chan][type]
                marker = np.array([chan, self.data_types[type]['nidx'], chan], dtype=dat.dtype)
                dat = np.concatenate((marker, dat))
                total_chans += 1
                if len(out) == 0:
                    out = dat.reshape(1,-1)
                    continue
                out = np.row_stack((out, dat))
        if len(out) == 0:
            return
        filename = f"capture.{'.'.join(types)}.{total_chans}.dat"
        filepath = os.path.join('results', self.uut.uut, filename)
        with open(filepath, 'w') as f:
            print(f"Saving data to {filepath}")
            self.dat_file = filepath
            out.T.tofile(f)
        print(f"""hexdump -e '{total_chans}/4 "%04x," "\\n" ' {filepath}""")

    def check_PWR_sync(self):
        testname = f"sync"
        type = 'PWR'
        if type not in self.data[self.active_chans[0]]:
            PR.Red('Unable to check sync no PWR')
            return
        self.results.register(testname)
        zero_crossings = {}
        for chan in self.active_chans:
            chandata = self.data[chan][type][100:]
            chandata = chandata - int(np.max(chandata) / 2)
            zc = np.where(np.diff(np.sign(chandata)))[0]
            mask = np.concatenate([[np.inf], np.diff(zc)]) > 1
            if len(mask) == 1:
                mask = []
            zero_crossings[chan] = zc[mask]

        for chan, dat in zero_crossings.items():
            if not hasattr(self, 'dat0'):
                self.dat0 = dat
                self.chan0 = chan
                continue
            if len(dat) == 0:
                self.results.failed(chan)
                PR.Red(f"Fail: CH{chan} no zero crossings")
                continue
            try:
                comparison = np.allclose(self.dat0, dat, atol=2, rtol=0)
            except Exception as e:
                print(e)
                self.results.failed(chan)
                PR.Red(f"Fail: CH{self.chan0} CH{chan} comparison failed")
                continue
            if comparison:
                self.results.passed(chan)
                PR.Green(f"Pass: CH{self.chan0} CH{chan} in sync")
            else:
                self.results.failed(chan)
                PR.Red(f"Fail: CH{self.chan0} CH{chan} not in sync")

    def check_capture(self):
        print()
        PR.Reverse('Capture results:')
        if 'sync' in self.results.arr:
            failures = sorted(self.results.arr['sync']['fail'])
            if len(failures) == 0:
                PR.Green(f"All channels in sync")
            else:
                PR.Red(f"Channels {','.join(list(map(str, failures)))} out of sync")
        self.plot_data()

    def get_loc(self, chan):
        return ((chan + 7) // 8)

    def plot_data(self, chans=None, plots=None):
        for type in self.args.dtypes:
            if type not in self.data_types:
                PR.Red(f"data type {type} is invalid")
                continue
            print(f"Plotting {type}")
            dtype = self.data_types[type]
            if not plots:
                plots = self.args.foils
            figure, axis = plt.subplots(plots)
            plt.suptitle(f"{type} Bolo[{self.args.bolo}]")
            if plots == 1:
                axis = [axis]
                fidx = 0
            for chan in self.data:
                if chans and chan not in self.active_chans:
                    continue
                chan_idx = chan - 1
                if plots > 1:
                    fidx = (chan_idx - ((chan_idx  // self.args.foils) * self.args.foils))
                    title = f"foil {fidx + 1}"
                axis[fidx].plot(self.data[chan][type][100:self.args.ptotal] * dtype['scaler'], label=f"{type} CH {chan}", linewidth=1, color=self.get_color(chan_idx))
                axis[fidx].set_ylabel(dtype['unit'])
                if plots == 1:
                    title = f"Foils {self.args.foils}"
                axis[fidx].set_title(title)
                axis[fidx].legend()
        plt.tight_layout()
        plt.show()

    #helper classes

    class StrobeHelper:
        def __init__(self, uut):
            self.uut = uut
            self.stop()

        def start(self):
            print('Priming strobe')
            self.uut.s0.GPG_ENABLE = '0'
            self.uut.s0.SIG_EVENT_SRC_1 = 'GPG'
            self.uut.s0.GPG_TRG = '1'
            self.uut.s0.GPG_TRG_DX = '1'
            self.uut.s0.GPG_TRG_SENSE = '1'
            self.uut.s0.SIG_FP_GPIO = '2'
            self.uut.s0.GPG_MODE = '0'
            #self.uut.s0.gpg_timescaler = '625' #20Hz
            self.uut.s0.gpg_timescaler = '6250' #2Hz
            self.uut.load_gpg('\n'.join(DEFAULT_STL))
            self.uut.s0.GPG_ENABLE = '1'

        def stop(self):
            self.uut.s0.GPG_ENABLE = '0'

    class ResultHelper:
        arr = {}
        current = None
        def register(self, testname):
            self.current = testname
            if testname in self.arr:
                return
            self.arr[testname] = {'pass' : [],'fail' : []}

        def passed(self, chans):
            self.add('pass', chans)

        def failed(self, chans):
            self.add('fail', chans)

        def add(self, result, chans):
            if type(chans) is not list:
                chans = [str(chans)]
            results = self.arr[self.current][result]
            for chan in chans:
                if chan not in results:
                    results.append(str(chan))
        
        def get(self):
            for type in self.arr:
                for result in self.arr[type]:
                    self.arr[type][result] = sorted(self.arr[type][result])
            return self.arr

    #save funcs

    def get_uut_config(self):
        uut = self.uut
        software_version = uut.s0.software_version
        fpga_version = uut.s0.fpga_version
        config = {
            'uut_name'       : uut.uut,
            'fpga'           : fpga_version.split(' ')[0],
            'fpga_timestamp' : fpga_version.split(' ')[-1],
            'version'        : int(software_version.split('-')[1]),
            'firmware'       : software_version,
            'serial'         : uut.s0.SERIAL,
            'model'          : uut.s0.MODEL,
            'clk'            : int(float(acq400_hapi.pv(uut.s0.SIG_CLK_S1_FREQ))),
            'data_size'      : uut.data_size(),
            'modules'        : []
        }
        for site_i in uut.s0.sites.split(','):
            site = getattr(uut, f"s{site_i}")
            module = {
                'model': site.MODEL,
                'serial' : site.SERIAL,
                'nchan' : int(site.NCHAN),
                'full_model' : site.PART_NUM,
                'location' : int(site_i),
            }
            config['modules'].append(module)
        return config

    def get_test(self):
        return {
            'type'     : 'bolo',
            'bolo_id'  : self.args.bolo,
            'cycles'   : f"{self.cycle}/{self.args.cycles}",
            'channels' : ','.join(list(map(str, self.channels))),
            'foils'    : self.args.foils,
        }
    
    def get_color(self, chan):
        colors = ['#0111B5', '#EC151D', '#21B321', '#120413', '#7C35BB', '#FFC800', '#ED17C0', '#FB6F42', '#12969B']
        return colors[chan % len(colors)]

    def get_calibration(self):
        if len(self.calibration) > 0:
            return self.calibration
        return None
    
    def gen_filepath(self, ext):
        path = os.path.join('results', self.uut.uut, self.timestamp)
        filename = f"{self.uut.uut}.{self.args.bolo}.{ext}"
        try:os.makedirs(path)
        except:pass
        return os.path.join(path, filename)
    
    def send_to_remote(self, payload):
        url = self.args.url
        if not url.startswith('http'):
            url = f"http://{url}"
        if not url.endswith('/'):
            url = f"{url}/"

        print(f'Sending results to {url}')

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code != 200:
            PR.Red(f'Error: {r.status_code}')
            print(r.text)
            return
        #print(r.text)
        PR.Green('Results sent successfully')
        if not self.dat_file:
            return
        
        r = requests.post(url, files={"dat_file": open(self.dat_file, "rb")})
        if r.status_code != 200:
            PR.Red(f'Error: {r.status_code}')
            print(r.text)
            return
        #print(r.text)
        PR.Green('Datfile sent successfully')

    def save_results(self):
        if len(self.data) == 0 and len(self.calibration) == 0:
            exit()
        self.beep_beeper(3)

        if self.args.cal:
            self.check_calibration()
            self.print_cal()
            if self.args.tocsv:
                self.cal_to_csv()

        if self.args.cap:
            if self.args.save:
                self.save_data()
            self.check_capture()
        
        payload = {
            'uut'         : self.get_uut_config(),
            'test'        : self.get_test(),
            'results'     : self.results.get(),
            'calibration' : self.get_calibration(),
            'v'           : 4
        }

        filepath = self.gen_filepath('json')
        with open(filepath, 'w') as f:
            print(f"Saving test config to {filepath}")
            json.dump(payload, f, indent=4)

        if self.args.url:
            self.send_to_remote(payload)

#execution starts here
def run_main(args):
    bh = bolo_handler(args)
    
    try:
        for chanset in bh.chanset:

            bh.set_active(chanset)
            bh.ask_if_connected()
            time_start = time.time()

            for cycle in range(1, args.cycles + 1):
                bh.set_cycle(cycle)

                if args.cal:
                    bh.run_cal()

                if args.cap:
                    bh.run_cap()

            total_time = time.time() - time_start
            print(f"{args.cycles} cycles took {total_time:.2f}s")

    except KeyboardInterrupt as e:
        print('Stopping')

    bh.strobe.stop()
    bh.save_results()

if __name__ == '__main__':
    run_main(get_parser().parse_args())
