#!/usr/bin/env python3


"""
Tests anatrg with sg and awg

Usage:

    ./test_apps/anatrg_demo.py --ai=acq1102_009 --ao=acq2106_133 --pause=0 --test=awg
    ./test_apps/anatrg_demo.py --ai=acq1102_009 --ao=acq2106_133 --pause=0 --test=sg --siggen=SG0153

"""
import argparse
import epics
import time
from acq400_hapi import factory, Agilent33210A, PR, pv, pprint
from epics import caget, caput, caput_many

from user_apps.utils.wavegen import WaveGen


#helper classes
class AnatrgMonitor():
    triggered = set({})
    pvs = {}

    def __init__(self, uutname, site, channels):
        self.pvbase = f"{uutname}:{site}:ANATRG:LIVE:"
        self.ready = False
        self.group_triggers = 0

        self.pvs['group'] = epics.PV(f"{uutname}:0:SIG:TRG_MB:COUNT")
        self.pvs['group'].add_callback(self.group_callback)

        for chan in channels:
            pvname = f"{self.pvbase}{chan:02}"
            pv = epics.PV(pvname, auto_monitor=epics.dbr.DBE_VALUE)
            pv.add_callback(self.triggered_callback)
            self.pvs[chan] = pv

        while not all(pv.connected for pv in self.pvs.values()):
            print('Waiting until pvs connected')
            time.sleep(0.5)

    def triggered_callback(self, pvname=None, value=None, **kwargs):
        if not self.ready: return
        if int(value) == 0: return 
        chan = pvname.removeprefix(self.pvbase)
        print(f"{pvname} triggered")
        self.triggered.add(int(chan))

    def group_callback(self, pvname=None, value=None, **kwargs):
        if not self.ready: return
        self.group_triggers += 1

    def monitor(self):
        self.triggered.clear()
        self.ready = True

    def read(self):
        self.ready = False
        return self.triggered
    
    def wait_for_change(self, timeout=10):
        t0 = time.time()
        while True:
            if len(self.triggered) > 0:
                time.sleep(1)
                return
            if time.time() - t0 > timeout:
                PR.Red("Error: Timeout")
                return
            print('Waiting for event')
            time.sleep(1)
    
class AnatrgHelper():

    def __init__(self, uutname, site):
        self.pvbase = f"{uutname}:{site}:ANATRG:"

    def set(self, channels, level1, level2=None, group=None, mode="rising"):
        print(f"Setting Chans {channels} {level1}V {mode} group {group}")
        map = {}
        chan_mode = "{pvbase}{chan:02}:M"
        chan_level1 = "{pvbase}{chan:02}:L1"
        chan_level2 = "{pvbase}{chan:02}:L2"
        chan_group = "{pvbase}GROUP:{chan:02}"
        
        for chan in channels:
            map[chan_mode.format(pvbase=self.pvbase, chan=chan)] = mode
            map[chan_level1.format(pvbase=self.pvbase, chan=chan)] = level1
            if level2 != None: map[chan_level2.format(pvbase=self.pvbase, chan=chan)] = level2
            if group != None: map[chan_group.format(pvbase=self.pvbase, chan=chan)] = group

        caput_many(map.keys(), map.values(), wait=True)

    def set_group_mode(self, group=0):
        caput(f"{self.pvbase}GROUP_MODE", group)

    def set_all(self, level1=0, level2=0, mode='none'):
        print(f"Setting all {level1}V {level2}V {mode}")
        caput(f"{self.pvbase}ALL:L1", level1)
        caput(f"{self.pvbase}ALL:M", mode)
        caput(f"{self.pvbase}ALL:L2", level2)
        caput(f"{self.pvbase}ALL:SET", 1)

    def group_all(self, group=True):
        if group:
            caput(f"{self.pvbase}GROUP:ALL:SET", 1)
        else:
            caput(f"{self.pvbase}GROUP:ALL:CLR", 1)


#helper funcs
def wait_for_event(uut):
    while True:
        if int(pv(uut.s0.SIG_EVT_EXT_COUNT)) > uut.evnt0:
            return
        time.sleep(1)

def wait_for_segment(uut, segment):
    while True:
        segcurr = pv(uut.s5.AWG_SEG)
        if segment == segcurr:
            print(f"Segment is {segment}")
            return
        uut.s0.soft_trigger = 1
        time.sleep(1)

def wait_for_run(uut):
    started = False
    while pv(uut.s0.CONTINUOUS_STATE) != 'RUN':
        if not started:
            uut.s0.CONTINUOUS = 1
            started = True
        time.sleep(1)

def get_groups(max, total):
    groups = []
    for i in range(1, total + 1):
        group = list(range(i, max + 1, total))
        groups.append(group)
    return groups

def get_segments(char):
    return [chr(i) for i in range(ord('A'), ord(char) + 1)]


#siggen test
def run_sg_test(ai_uut, args):

    siggen = Agilent33210A(args.sg)
    siggen.send("TRIG:SOUR EXT")
    siggen.send("BURS:STAT ON")
    
    nchan = int(ai_uut[args.awg_site].NCHAN)
    channels = list(range(1, nchan + 1))
    print(f"Testing {ai_uut.uut} Site {args.sg_site} using {args.sg}")

    ana = AnatrgHelper(ai_uut.uut, args.sg_site)
    mon = AnatrgMonitor(ai_uut.uut, args.sg_site, channels)
    ana.set_all()
    ana.group_all(False)
    time.sleep(5)

    groups = get_groups(nchan, 8)
    for chans in groups:
        print(f"\nTesting channels {chans}")

        ai_uut.evnt0 = int(pv(ai_uut.s0.SIG_EVT_EXT_COUNT))
        ana.set(chans, 5, mode="rising", group=args.group)
        time.sleep(2) #needed
        mon.monitor()
        group_triggers = mon.group_triggers

        siggen.trigger()
        mon.wait_for_change()
        time.sleep(1)

        trg_chans = mon.read()
        trg_chans = sorted(list(trg_chans))
        if trg_chans == chans: PR.Green(f"Success expected {chans} got {trg_chans}")    
        else: PR.Red(f"Error expected {chans} got {trg_chans}")

        if args.group and mon.group_triggers > group_triggers: PR.Green(f"Group Triggered") 
        elif args.group : PR.Red(f"Group failed to trigger")

        ana.set(chans, 0, mode="none", group=False)

        if args.pause:
            input('Press any key to continue . . .')
    ana.set_all()


#awg test
def run_awg_test(ao_uut, ai_uut, args):
    print(f"Testing {ai_uut.uut} Site {args.awg_site} using {ao_uut.uut} Site {args.ao_site}")
    
    waveargs = {
        'nchan': 32,
        'wavelength': 4000,
        'totallength': 20000,
        'scale': 0.1,
        "offset": "+8:1,-1",
    }

    nchan = int(ai_uut[args.awg_site].NCHAN)
    segments = get_segments(args.max_seg)
    groups = get_groups(nchan, len(segments))
    channels = list(range(1, nchan + 1))

    wait_for_run(ai_uut)

    ana = AnatrgHelper(ai_uut.uut, args.awg_site)
    mon = AnatrgMonitor(ai_uut.uut, args.awg_site, channels)

    ana.set_all()
    for idx, chans in enumerate(groups):
        level = 8.5 - idx
        ana.set(chans, level1=level, mode='rising')

    if args.group:
        ana.group_all()
        ana.set_group_mode(1)

    time.sleep(10) #needed

    for idx, chans in enumerate(groups):

        segment = segments[idx]
        chans_str = ','.join(map(str, chans))
        waveargs['wave'] = f"NULL:ALL/SINE:{chans_str}"
        waveform = WaveGen(**waveargs)
        waveform.generate(hush=True)

        if args.plot:
            waveform.plot()
        print(f"Uploading waveform to segment {segment}")
        ao_uut.load_awg(waveform.data, segment=segment)

    ao_uut.s0.soft_trigger = 1

    while True:
        group_triggers = mon.group_triggers
        for idx, chans in enumerate(groups):
            
            wait_for_run(ai_uut)

            print(f'\nTesting channels {chans}')
            segment = segments[idx]
            ao_uut.set_segment(segment)
            wait_for_segment(ao_uut, segment)

            mon.monitor()
            print(f"Triggering {ao_uut.uut}")
            ao_uut.s0.soft_trigger = 1 

            mon.wait_for_change()
            trg_chans = mon.read()
            trg_chans = sorted(list(trg_chans))

            if trg_chans == chans: PR.Green(f"Success expected {chans} got {trg_chans}")    
            else: PR.Red(f"Error expected {chans} got {trg_chans}")
            
            if args.pause:
                input('Press any key to continue . . .')

        if args.group and mon.group_triggers > group_triggers: PR.Green(f"Success history group triggered") 
        elif args.group: PR.Red(f"Error history group did not triggered")


def get_parser():    
    parser = argparse.ArgumentParser(description="anatrg demo script")

    parser.add_argument('--test', default="awg", help="awg or sg")

    parser.add_argument('--ao', help="ao uut", required=True)
    parser.add_argument('--ao_site', default=6, type=int, help="ao uut ao site")

    parser.add_argument('--ai', help="acq uut hostname", required=True)
    parser.add_argument('--awg_site', default=1, type=int, help="ai uut site connected to awg")
    parser.add_argument('--sg_site', default=2, type=int, help="ai uut site connected to sg")

    parser.add_argument('--sg', default="SG0153", help="siggen hostname")
    parser.add_argument('--group', default=1, type=int, help="Test group triggering")
    parser.add_argument('--max_seg', default='H', help="last segment")
    parser.add_argument('--plot', default=0, type=int, help="Plot wavefrom")
    parser.add_argument('--pause', default=1, type=int, help="Pause between each loop")
    return parser

#starts here
def run_main(args):
    print(args)

    ao_uut = factory(args.ao)
    ai_uut = factory(args.ai)

    if args.test == 'sg':
        run_sg_test(ai_uut, args)

    if args.test == 'awg':
        run_awg_test(ao_uut, ai_uut, args)

if __name__ == '__main__':
    run_main(get_parser().parse_args())