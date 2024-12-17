#!/usr/bin/env python3


"""
anatrg awg loop

Usage:

    ./test_apps/anatrg_demo.py --ai=acq1102_009 --ao=acq2106_133
"""
import argparse
import time
from acq400_hapi import factory, pv, Agilent33210A
from epics import caget, caput, caput_many

from user_apps.utils.wavegen import WaveGen

#classes
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

class DotDict(dict):
    __delattr__ = dict.__delitem__
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

#helper funcs
def wait_for_segment(uut, segment):
    while True:
        segcurr = pv(uut.s1.AWG_SEG)
        if segment == segcurr:
            return
        uut.s0.soft_trigger = 1
        time.sleep(0.5)

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

#starts here
def run_main(args):
    print(args)

    ao_uut = factory(args.ao)
    ai_uut = factory(args.ai)

    EvtSrc = DotDict({'TRG': 0, 'MOD': 3})

    print(f"Testing {ai_uut.uut} Site {args.awg_site} using {ao_uut.uut} Site {args.ao_site}")
   
    waveargs = {
        'nchan': 4,
        'wavelength': 500,
        'totallength': 20000,
        'scale': args.scale,
        'offset': args.offset,
        'spos': args.spos,
        'wave': 'SINE:ALL'
    }

    nchan = int(ai_uut[args.awg_site].NCHAN)
    segments = get_segments(args.max_seg)
    groups = get_groups(nchan, 8)
    ai_uut.s0.evt_src_d0 = EvtSrc[args.ebs0]
    
    wait_for_run(ai_uut)

    if not args.leave_atd:
        ana = AnatrgHelper(ai_uut.uut, args.awg_site)
        ana.set_all()

        for idx, chans in enumerate(groups):
            level = 8.5 - idx
            ana.set(chans, level1=level, mode='rising')
            time.sleep(1)

    pretrg = pv(ao_uut.s0.SIG_SRC_TRG_0)
    pretrg = pretrg if pretrg != 'NONE' else 'EXT'
    ao_uut.s0.SIG_SRC_TRG_0 = 'NONE' #prevent crash
    time.sleep(2)

    for segment in segments:
        print(f'create segment {segment}')
        if segment != 'A':
            chans = groups.pop(0)
            chans_str = ','.join(map(str, chans))
            waveargs['wave'] = f"NULL:ALL/SINE:{chans_str}"

        waveform = WaveGen(**waveargs)
        waveform.generate(hush=True)
        if args.plot:
            waveform.plot()

        if not args.noload:
            print(f"Uploading waveform to segment {segment}")
            ao_uut.load_awg(waveform.data, segment=segment)
    
    ao_uut.s0.SIG_SRC_TRG_0 = pretrg

    while True:
        for segment in segments:
            print(f"Setting segment {segment} as active")
            ao_uut.set_segment(segment)

            if args.pause:
                input('Press Enter to continue . . .')
            else:
                time.sleep(1)

def get_parser():    
    parser = argparse.ArgumentParser(description="anatrg demo script")

    parser.add_argument('--ao', help="ao uut", required=True)
    parser.add_argument('--ao_site', default=5, type=int, help="ao uut ao site")

    parser.add_argument('--ai', help="acq uut hostname", required=True)
    parser.add_argument('--awg_site', default=1, type=int, help="ai uut site connected to awg")

    parser.add_argument('--max_seg', default='I', help="last segment")
    parser.add_argument('--plot', default=0, type=int, help="Plot wavefrom")
    parser.add_argument('--pause', default=0, type=int, help="Pause between each loop")
    parser.add_argument('--ebs0', default="MOD", help="event bus source d0")

    parser.add_argument('--offset', default="+8:1,-1", help="waveform voltage offset")
    parser.add_argument('--spos', default="+0:4000,500", help="waveform start position")
    parser.add_argument('--scale', default="0.2", help="waveform voltage scale")
    parser.add_argument('--noload', default=0, help="don't load the WF (maybe already done)")
    parser.add_argument('--leave_atd', default=0, help="dont' change atd settings (maybe already done)")
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
