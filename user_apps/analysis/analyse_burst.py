#!/usr/bin/env python3
'''
Created on 20 Jul 2023

@author: pgm
'''

import numpy as np
import matplotlib.pyplot as plt
import argparse

import hashlib

from prettytable import PrettyTable

ES_MAGIC0   = 0xaa55f154
ES_MAGIC1   = 0xaa55f15f
ES_SAMPLE   = 4
ES_CLK      = 5
ES_SAMPLE2  = 6
ES_CLK2     = 7

ES_MAGIC0_FIELDS = ( 0,  1,  2,  3,  8,  9, 10, 11)
ES_MAGIC1_FIELDS = (16, 17, 18, 19, 24, 25, 26, 27, 
                    32, 33, 34, 35, 40, 41, 42, 43,
                    48, 49, 50, 51, 56, 57, 58, 59)




class ES_STATS:
    the_stats = []
    the_raw_ix = []
    the_sample_counts = []
    the_clk_counts = []
    
    def __init__(self, _es_fields):
        self.iraw = _es_fields[0]
        self.sample = _es_fields[1]
        self.clk = self.clk = _es_fields[2]
        self.my_id = len(ES_STATS.the_stats)
        
        
        if self.my_id == 0:
            self.d_iraw = 0
            self.d_sample = 0
            self.d_clk = 0
        else:
            es1 = ES_STATS.the_stats[-1]
            self.d_iraw = self.iraw - es1.iraw
            self.d_sample = self.sample - es1.sample
            self.d_clk = self.clk - es1.clk
        ES_STATS.the_stats.append(self)
        
    def print(self):
        print(f'ES_STATS {self.my_id} {self.iraw} {self.sample} {self.clk}')
        
    def print_all():
        t = PrettyTable(['ii', 'iraw', 'sample', 'clk', 'delta_iraw', 'delta_sample', 'delta_clk'], border=False)
        for ii, ess in enumerate(ES_STATS.the_stats):
            t.add_row((ii, ess.iraw, ess.sample, ess.clk, ess.d_iraw, ess.d_sample, ess.d_clk))
        print(t)
        
    def is_valid():
        model_d_sample = ES_STATS.the_stats[1].d_sample
        model_d_clk = ES_STATS.the_stats[1].d_clk
        sample_fail_count = 0
        clk_fail_count = 0
        for ii, es in enumerate(ES_STATS.the_stats[2:]):
            if es.d_sample != model_d_sample:
                print(f'ERROR: ES fail at {ii} NSAM: expected{model_d_sample} got {es.d_sample}')
                sample_fail_count += 1
            if es.d_clk > model_d_clk and (es.d_clk - model_d_clk) > 1:
                print(f'ERROR: ES fail > at {ii} diff: {es.d_clk - model_d_clk} CLK: expected{model_d_clk} got {es.d_clk}')
                clk_fail_count += 1
            if es.d_clk < model_d_clk and (model_d_clk - es.d_clk) > 1:
                print(f'ERROR: ES fail < at {ii} diff: {model_d_clk - es.d_clk} CLK: expected{model_d_clk} got {es.d_clk}')
                clk_fail_count += 1                
                
        return (sample_fail_count == 0 and clk_fail_count == 0, ii, sample_fail_count, clk_fail_count)

    def get_raw_ix():
        if len(ES_STATS.the_raw_ix) < len(ES_STATS.the_stats):
            ES_STATS.the_raw_ix = [ es.iraw for es in ES_STATS.the_stats]
        return ES_STATS.the_raw_ix

    def get_sample_counts():
        if len(ES_STATS.the_sample_counts) < len(ES_STATS.the_stats):
            ES_STATS.the_sample_counts = [ es.sample for es in ES_STATS.the_stats]
        return ES_STATS.the_sample_counts 

    def get_clk_counts():
        if len(ES_STATS.the_clk_counts) < len(ES_STATS.the_stats):
            ES_STATS.the_clk_counts = [ es.clk for es in ES_STATS.the_stats]
        return ES_STATS.the_clk_counts    

    def get_blen():
        return ES_STATS.the_stats[1].d_sample

            
def is_valid_es(iraw, es):
# return if this is an ES, load it and return True FAIL fast!  
# we pre-filtered es[0] == ES_MAGIC0, so we expect all PASS
    for ii in ES_MAGIC0_FIELDS[1:]:
        if es[ii] != ES_MAGIC0:
            print(f'ES match fail at {iraw},{ii} expect:{ES_MAGIC0:08x} got:{es[ii]:08x}')
            return False
    for ii in ES_MAGIC1_FIELDS:
        if es[ii] != ES_MAGIC1:
            print(f'ES match fail at {iraw},{ii} expect:{ES_MAGIC1:08x} got:{es[ii]:08x}')
            return False
    if es[ES_SAMPLE] != es[ES_SAMPLE2]:
        print(f'ES match fail at {iraw},{ii} SAMPLE changed {es[ES_SAMPLE]} {es[ES_SAMPLE2]}')
        return False
    if es[ES_CLK] != es[ES_CLK2]:
        print(f'ES match fail at {iraw},{ii} CLK changed {es[ES_CLK]} {es[ES_CLK2]}')
        return False
    
    ES_STATS((iraw, es[ES_SAMPLE], es[ES_CLK]))
    return True           
            
    
DATA='nodata'          
        
def analyse_es(args, raw_es):
    print(f'raw_es.shape:{raw_es.shape}')
    esx = np.nonzero(raw_es[:,0] == ES_MAGIC0)
    print(f'type esx {type(esx)}')
    
    valid_es = []
    for ix in esx[0]:
#        print(f'ix={ix}')
        es = raw_es[ix,:]
#        print(f'es.shape:{es.shape}')
        if args.verbose > 1:
            with np.printoptions(formatter={'int':hex}):
                print(es)
 
        if not is_valid_es(ix, es):
            print(f"Warning: invalid es at {ix}")
    
    if args.verbose:
        ES_STATS.print_all()
    es_valid = ES_STATS.is_valid()
    if es_valid[0]:
        print(f'{DATA} ES Analysis: {es_valid[1]} PASS')
    else:
        print(f'{DATA} ES Analysis: {es_valid[1]} PASS {es_valid[2]} sample FAIL {es_valid[3]} clk FAIL')

def sample_count_plot(ax):
    ax.set_title(f'Plot of burst first sample count ES[{ES_SAMPLE}]')
    ax.plot(ES_STATS.get_sample_counts())
    
def timing_plot(ax):
    #ax1.figure()
    #ax1.title(f'Plot of burst start time in sample clocks\n{DATA}')
    #ax1.ylabel('clocks')
    #ax1.xlabel('burst number')
    ax.set_title(f'Plot of burst start time in sample clocks ES[{ES_CLK}]')
    ax.plot(ES_STATS.get_clk_counts())

    
def stack_plot(raw_adc, raw_ix, ch, ax, label='', delta=False, stackoff=0):
    print(f'stack_plot {ax}')
    blen = ES_STATS.get_blen()
    nburst = len(raw_ix)
    print(f'PLOT nburst {len(raw_ix)} burst_len {blen} ch {ch}')
    
    x = range(1, blen)

    #plt.figure()
    #plt.title(f'{label} Stack plot of {nburst} bursts\n{DATA}')
    ax.set_title(f'{label} Stack plot of {nburst} bursts')
    #plt.ylabel('ADC codes')
    #plt.xlabel('samples in burst')

    for ii, brst in enumerate(raw_ix):
        try:
            y = raw_adc[brst+1:brst+blen,ch]+ stackoff*ii
            if delta:
                if ii == 0:
                    y0 = y
                y = y - y0

            if len(x) == len(y):
                ax.plot(x, y, label=f'{ii}')
        except ValueError:
           pass

def correlate(raw_adc, raw_ix, ch0, _atol, _rtol):
    ref = ch0[0]
    matches = {}
    ref = {}
    blen = ES_STATS.get_blen()

    for ic in ch0:
        matches[ic] = []

    for ib, brst in enumerate(raw_ix):
        for icn, ic in enumerate(ch0):
#            print(f'{ib},{icn} ch:{ic+1} brst:{brst}')
            try:
                y = raw_adc[brst+1:brst+blen, ic]
                if ib==0:
                    ref[ic] = y
                match = np.allclose(y, ref[ic], atol=_atol, rtol=_rtol)
#                print(f'[{ib}],[{ic}] : {match}')
                matches[ic].append(match)
            except ValueError:
                pass 

    all_good = all([all(matches[ic]) for ic in ch0])
    print('CORRELATE {}'.format('PASS: All Channels Match' if all_good else 'FAIL: Not all channels match'))
    t = PrettyTable([f'{ch+1:02d}' for ch in ch0], border=False)
    t.add_row(['T' if all(matches[ic]) else 'F' for ic in ch0])
    print(t)

def plot_timeseries(raw_adc, ch, ax, label):
    #plt.figure()
    #plt.title(f'{label} Time-series plot of CH{ch}\n{DATA}')    
    #plt.ylabel('ADC codes')
    #plt.xlabel('sample') 
    yraw = raw_adc[:,ch]
    y_no_es = np.delete(yraw, ES_STATS.get_raw_ix())
    x = range(0, len(y_no_es))
    ax.set_title(f'{label} Time-series plot of CH{ch}') 
    ax.plot(x, y_no_es, label=f'CH{ch}')

def analyse(args):
    global STACKOFF
    STACKOFF = args.stack_off
    fname = args.data[0]
    raw_adc = np.fromfile(fname, dtype=args.np_data_type)
    ll = len(raw_adc)//args.nchan
    raw_adc = raw_adc[0:ll*args.nchan]
    raw_es = raw_adc.view(np.uint32)
    
    raw_adc = np.reshape(raw_adc, (ll, args.nchan))
    raw_es  = np.reshape(raw_es,  (ll, args.ess))
    
    print(f"raw_adc {raw_adc.shape}")
    print(f"raw_es  {raw_es.shape}")

    if args.print_hash:
        m = hashlib.sha1()
        m.update(raw_adc)
        print(f'fname {fname} sha1:{m.hexdigest()}')

    analyse_es(args, raw_es)
    
    c1, c2, _atol, _rtol = args.check_range
    correlate(raw_adc, ES_STATS.get_raw_ix(), [ch-1 for ch in range(c1, c2+1) ], _atol, _rtol)

#    correlate(raw_adc, ES_STATS.get_raw_ix(), (1,2,3,4,5,6,7,8,33,34))
    if args.stack_plot > 0:
        fig, axx = plt.subplots(3, 2, figsize=(12,10))
        fig.suptitle(f'Burst Mode Test: {DATA}')
        sample_count_plot(axx[0][0])
        timing_plot(axx[1][0])
        
        stack_plot(raw_adc, ES_STATS.get_raw_ix(), args.stack_plot-1, axx[0][1], f'signal CH{args.stack_plot}', stackoff=args.stack_off)
        stack_plot(raw_adc, ES_STATS.get_raw_ix(), args.stack_plot-1, axx[1][1], f'diff signal CH{args.stack_plot}', delta=True, stackoff=args.stack_off)
        
        if args.fiducial_plot:
            plot_timeseries(raw_adc, args.fiducial_plot-1, axx[2][0], f'fiducial CH{args.fiducial_plot}')
            stack_plot(raw_adc, ES_STATS.get_raw_ix(), args.fiducial_plot-1, axx[2][1], f'fiducial CH{args.fiducial_plot}')

        plt.show()
    return (raw_adc, raw_es)

def get_parser():
    parser = argparse.ArgumentParser(description='rgm plot demo')
    parser.add_argument('--nchan', type=int, default=32)
    parser.add_argument('--data_type', type=int, default=None, help='Use int16 or int32 for data demux.')
    parser.add_argument('--verbose', type=int, default=0, help='increase verbosity')
    parser.add_argument('--stack_plot', type=int, default=0, help='if non zero, make a stack plot of selected channel')
    parser.add_argument('--stack_off', type=int, default=0, help='offset each element in stack to make a waterfall chart')
    parser.add_argument('--check_range', type=str, default='1,1', help='c0,c1,[atol,rtol] : range of channels to check, atol, rtol: see numpy.rclose')
    parser.add_argument('--print_hash', type=int, default=0, help='print sha1 of the file (protect against possibility of duplicate data')
    parser.add_argument('--fiducial_plot', type=int, default=0, help='if non zero, make a stack plot of selected channel')
    parser.add_argument('--uut', help='uut for title')
    parser.add_argument('data', nargs=1, help="data ")
    return parser
 
def fix_args(args):
    global DATA
    if args.data_type == 16:
        args.np_data_type = np.int16
        args.WSIZE = 2
        args.ess = args.nchan//2
    elif args.data_type == 8:
        args.np_data_type = np.int8
        args.WSIZE = 1
        rgs.ess = args.nchan//4
    else:
        args.np_data_type = np.int32
        args.WSIZE = 4
        args.ess = args.nchan
    args.ssb = args.nchan * args.WSIZE
    DATA = args.data[0]

    _check_range = [ int(ii) for ii in args.check_range.split(',')]
    args.check_range = [ 1, 1, 250, 1 ]
    for ix, val in enumerate(_check_range):
       args.check_range[ix] = val
  
    print(f'processing {DATA}')
    return args

   
def run_main():
    analyse(fix_args(get_parser().parse_args()))

# execution starts here

if __name__ == '__main__':
    run_main()
