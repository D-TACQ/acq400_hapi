
import argparse
import acq400

class Acq400UI:
    @staticmethod
    def exec_args_trg(uut, args, trg): 
        (typ, edge) = ('int', 'rising')
        try:
            (typ, edge) = trg.split(',')
        except:
            pass
        
        triplet = "1,%d,%d" % (0 if typ == 'ext' else 1, 0 if edge == 'falling' else 1)
        
        if args.pre == None or pre[0] != '0':
            u.s1.trg = "1,1,1"
            u.s1.event0 = triplet
        else:
            u.s1.trg = triplet
            u.s1.event0 = "0,0,0"                    
        
    @staticmethod
    def exec_args_clk(uut, clk):
        c_args = clk.split(',')
        src = c_args[0]
        
        if len(c_args) > 1:
            _hz = intSI(c_args[1])
            if len(c_args) > 2:
                _fin = intSI(c_args[2])
            else:
                _fin = 0
        else:
            _hz = 0
            
        if src == 'ext' or src == 'fpclk':
            uut.set_mb_clk(self, hz=_hz, src="fpclk", fin=_fin)
        elif src == 'int' or src == 'zclk':            
            uut.set_mb_clk(self, hz=_hz, src="zclk", fin=_fin)
        elif src == 'xclk':
            uut.set_mb_clk(self, hz=_hz, src="xclk", fin=_fin)
    
    @staticmethod    
    def set_simulate(uut, enable):
        for s in uut.modules:
            uut.modules[s].simulate = '1' if enable else '0'
            
    @staticmethod
    def exec_args_sim(uut, sim): 
        try:            
            sim_sites = [ int(s) for s in sim.split(',')]
            for site in uut.modules:
                sim1 = '1' if site in sim_sites else '0'
                uut.svc['s%s' % (site)].simulate = sim1
        #            print "site {} sim {}".format(site, sim1)
        except AttributeError:
            set_simulate(uut, sim)
    
        
    @staticmethod
    def exec_args_trace(uut, trace):
        for svn, svc in sorted(u.svc.items()):
            svc.trace = trace
            
    @staticmethod
    def add_args(parser):
        parser.add_argument('--clk', default=None, help='int|ext|zclk|xclk,fpclk,SR,[FIN]')
        parser.add_argument('--trg', default=None, help='int|ext,rising|falling')
        parser.add_argument('--sim', default=None, help='nosim|s1[,s2,s3..] list of sites to run in simulate mode')
        parser.add_argument('--trace', default=None, help='1 : enable command tracing')
        
    @staticmethod   
    def exec_args(uut, args):
        if args.trg:
            exec_args_trg(uut, args.trg)
        if args.clk:
            exec_args_clk(uut, args.clk)
        if args.sim:
            exec_args_sim(uut, args.sim)
        if args.trace:
            exec_args_trace(uut, args.trace)
            
    
        
 