#!/usr/bin/env python3

import argparse
import os

from acq400_hapi import acq400, intSI
from acq400_hapi.intSI import intSI_cvt
from acq400_hapi.intSI import intSIAction
from acq400_hapi.acq400_uut_handler import uut_handler
from acq400_hapi.debug import Debugger


class Acq400UI:
    """ Common UI features for consistent args handling across all apps
    """
    @staticmethod
    def _exec_args_trg(uut, args, trg):
#        print("exec_args_trg {}".format(trg))
        if trg == 'notouch':
            return
        (typ, edge) = ('int', 'rising')
        try:
            (typ, edge) = trg.split(',')
        except:
            typ = trg

        if typ == 'ext':
            dx = 0
        else:
            args.auto_soft_trigger = True
            dx = 1
            
        triplet = "1,%d,%d" % (dx, 0 if edge == 'falling' else 1)
        print("triplet={}".format(triplet))
        if args.pre != 0:
            uut.sA.trg = "1,1,1"
            uut.sA.event0 = triplet
            args.auto_soft_trigger = True
        else:
            uut.sA.trg = triplet
            uut.sA.event0 = "0,0,0"

    @staticmethod
    def _exec_args_clk(uut, clk):
        c_args = clk.split(',')
        src = c_args[0]
        _fin=1000000
        _hz=1000000


        if len(c_args) > 1:
            _hz = intSI_cvt(c_args[1])
            if len(c_args) > 2:
                _fin = intSI_cvt(c_args[2])

        if src == 'ext' or src == 'fpclk':
            uut.set_mb_clk(hz=_hz, src="fpclk", fin=_fin)
        elif src == 'int' or src == 'zclk':
            uut.set_mb_clk(hz=_hz, src="zclk", fin=_fin)
        elif src == 'xclk':
            uut.set_mb_clk(hz=_hz, src="xclk", fin=_fin)

    @staticmethod
    def _exec_args_sim(uut, sim):
        sim_sites = [ int(s) for s in sim.split(',')]
        for site in uut.modules:
            sim1 = '1' if site in sim_sites else '0'
            uut.svc['s%s' % (site)].simulate = sim1
        #            print "site {} sim {}".format(site, sim1)


    @staticmethod
    def _exec_args_trace(uut, trace):
        if trace is not None:
            for svn, svc in sorted(uut.svc.items()):
                svc.trace = trace

    @staticmethod
    def _exec_args_transient(uut, args):
        uut.configure_transient(pre=args.pre, post=args.post, \
            auto_soft_trigger=(1 if args.auto_soft_trigger or args.pre>0 else 0), demux=args.demux)

    executors = []

    @staticmethod
    def _exec_args_playtrg(uut, args):
        print("_exec_args_playtrg")
        for ps in uut.s0.distributor.split(' '):
            if ps.startswith('sites='):
                val = ps.split('=')[1]
                psite = int(val.split(',')[0])
                try:
                    if args.aosite is None:                       
                        args.aosite = psite
                except:
                    args.aosite = psite
                    pass                                   
        
        if args.playtrg is not None:
            ta = args.playtrg.split(',')
            if len(ta) == 2:
                tt = ta[0]
                edge = ta[1]
            else:
                tt = ta[0]
                edge = 'rising'
            uut.modules[psite].trg = '1,{},{}'.format(1 if tt == 'int' else 0, 1 if edge == 'rising' else 0)
        
        if args.playdiv is not None:
            uut.modules[psite].CLKDIV = args.playdiv
    
    @staticmethod
    def add_args(parser, transient=False, post=True, pre=True, uuts=False, demux=1, play=False):
        """ generate standard args list

        Args:
             post: set False to disable creating the arg, becomes client app resposibility

        """
        
        if transient is True:
            if pre:
                parser.add_argument('--pre', default=0, action=intSIAction, help='pre-trigger samples')
            if post:
                parser.add_argument('--post', default=100000, action=intSIAction, help='post-trigger samples')
            if demux > -1:
                parser.add_argument('--demux', default='{}'.format(demux), type=int, help='embedded demux')

        if uuts:
            parser.add_argument('uuts', nargs='+', action=uut_handler, help="uuts")

        parser.add_argument('--clk', default=None, help='int|ext|zclk|xclk,fpclk,SR,[FIN]')
        parser.add_argument('--trg', default=None, help='int|ext,rising|falling')
        parser.add_argument('--sim', default=None, help='s1[,s2,s3..] list of sites to run in simulate mode')
        parser.add_argument('--trace', default=None, help='1 : enable command tracing')
        parser.add_argument('--auto_soft_trigger', default=0, type=int, help='force soft trigger generation')
        parser.add_argument('--clear_counters', action='store_true', help='clear all counters SLOW')
        
        if play:
            parser.add_argument('--playtrg', default=None, help='int|ext,rising|falling')
            parser.add_argument('--aosite', default=None, type=int, help='Site of AO module')
            parser.add_argument('--playdiv', default=None, type=int, help="CLKDIV for play site")


    @staticmethod
    def exec_args(uut, args):
        """ and execute all the args
        """
#        print("exec_args" )
        if args.clear_counters:
            uut.clear_counters()
        if args.clk:
            Acq400UI._exec_args_clk(uut, args.clk)
        if args.sim:
            Acq400UI._exec_args_sim(uut, args.sim)
        if args.trace:
            Acq400UI._exec_args_trace(uut, args.trace)
        try:
            if args.pre is not None:
                Acq400UI._exec_args_transient(uut, args)
        except:
            args.pre = 0
            pass
        if args.trg:
            Acq400UI._exec_args_trg(uut, args, args.trg)
        try:
            if args.playtrg != None:
                Acq400UI._exec_args_playtrg(uut, args)
        except:
            pass
        
    @staticmethod
    def imported_defaults_overrider(parser, defaults):
        arr = parser._positionals._actions
        for x in arr:
            if x.dest in defaults.keys():
            #print("Overriding {} with {}".format(x.dest,defaults[x.dest]))
                x.default = defaults[x.dest]
        return parser
    
    @staticmethod
    def merge_parsers(parser, donor, overwrite=False, blacklist=[]):
        """Merges arguments from two argparser parsers"""
        blacklist = blacklist + ['h', 'help']
        existing = [a.dest for a in parser._actions]
        for action in donor._actions:
            dest = action.dest
            if dest in blacklist: continue
            if dest in existing and parser.conflict_handler == 'error':
                if overwrite:
                    for idx, a in enumerate(parser._actions):
                        if dest == a.dest:
                            parser._actions[idx] = action
                            for option in a.option_strings:
                                parser._option_string_actions[option] = action
                            break
                continue
            parser._add_action(action)
        return parser


class ArgTypes:
    @staticmethod
    def list_of_ints(value):
        """Converts 1,2,3 to [1,2,3]"""
        return list(map(int, value.split(',')))
    
    @staticmethod
    def list_of_strings(value):
        """Converts a,b,c to [a,b,c]"""
        return value.split(',')
    
    @staticmethod
    def list_of_channels(value):
        """Converts 1,2,6-8 to [1,2,6,7,8]"""
        if value.lower() == 'all': return 'all'
        channels = []
        for chan in value.split(','):
            if '-' in chan:
                start, end = map(int, chan.split('-'))
                channels.extend(list(range(start, end + 1)))
            else:
                channels.append(int(chan))
        return channels

    @staticmethod
    def int_with_unit(value):
        """Converts values with units to intergers"""
        units = {
            "k": 1e3,
            "M": 1e6,
            "G": 1e9,
            "kB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
        }

        scaler = 1
        for unit in units:
            if value.lower().endswith(unit.lower()):
                scaler = units.get(unit, 1)
                value = value[:-len(unit)]
                break
        return int(float(value) * scaler)

    @staticmethod
    def start_end_stride(value, default=(0, -1, 1)):
        """Converts start:end:stride into tuple"""
        value = value.strip().split(':')
        start = ArgTypes.int_with_unit(value[0]) if 0 < len(value) and value[0] else default[0]
        end = ArgTypes.int_with_unit(value[1]) if 1 < len(value) and value[1] else default[1]
        stride = ArgTypes.int_with_unit(value[2]) if 2 < len(value) and value[2] else default[2]
        assert(stride > 0)
        assert(end > start)
        return (start, end, stride)


def unit_test():

    # Testing start end stride
    assert(ArgTypes.start_end_stride('10:1000:100') == (10, 1000, 100))
    assert(ArgTypes.start_end_stride('1000:') == (1000, -1, 1))
    assert(ArgTypes.start_end_stride('1000::') == (1000, -1, 1))
    assert(ArgTypes.start_end_stride(':1000') == (0, 1000, 1))
    assert(ArgTypes.start_end_stride(':1000:') == (0, 1000, 1))
    assert(ArgTypes.start_end_stride('::1000') == (0, -1, 1000))
    assert(ArgTypes.start_end_stride(':') == (0, -1, 1))
    assert(ArgTypes.start_end_stride('0:') == (0, -1, 1))
    assert(ArgTypes.start_end_stride('::') == (0, -1, 1))
    assert(ArgTypes.start_end_stride('1:2:3:4:5:6') == (1, 2, 3))
    assert(ArgTypes.start_end_stride('1K:1M:100K') == (1000, 1000000, 100000))


if __name__ == '__main__':
    unit_test()