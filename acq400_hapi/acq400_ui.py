
import argparse
import os

from . import acq400
from . import intSI
from .intSI import intSI_cvt
from .intSI import intSIAction
from . import acq400_uut_handler
from .acq400_uut_handler import uut_handler


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
#        print("triplet={}".format(triplet))
        if args.pre != 0:
            uut.s1.trg = "1,1,1"
            uut.s1.event0 = triplet
            args.auto_soft_trigger = True
        else:
            uut.s1.trg = triplet
            uut.s1.event0 = "0,0,0"

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
    def exec_args_playtrg(uut, args):
        if args.playtrg == None:
            return
        else:
            ta = args.playtrg.split(',')
            if len(ta) == 2:
                tt = ta[0]
                edge = ta[1]
            else:
                tt = ta[0]
                edge = 'rising'

        trg = '1,{},{}'.format(1 if tt == 'int' else 0, 1 if edge == 'rising' else 0)
        for ps in uut.s0.distributor.split(' '):
            if ps.startswith('sites='):
                try:
                    psite = 's' + (ps.split('=')[1].split(',')[0])
                    uut.svc[psite].trg = trg
                except:
                    print("WARNING, failed to split distributore sites")

    @staticmethod
    def add_argument_playtrg(parser):
        parser.add_argument('--playtrg', default=None, help='int|ext,rising|falling')



    @staticmethod
    def add_args(parser, transient=False, post=True, pre=True, uuts=False, demux=1):
        """ generate standard args list

        Args:
             post: set False to disable creating the arg, becomes client app resposibility

        """
        if transient:
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



    @staticmethod
    def exec_args(uut, args):
        """ and execute all the args
        """
#        print("exec_args" )
        if args.clk:
            Acq400UI._exec_args_clk(uut, args.clk)
        if args.sim:
            Acq400UI._exec_args_sim(uut, args.sim)
        if args.trace:
            Acq400UI._exec_args_trace(uut, args.trace)
        if args.trg:
            Acq400UI._exec_args_trg(uut, args, args.trg)
        if args.post != None:
            Acq400UI._exec_args_transient(uut, args)
        
