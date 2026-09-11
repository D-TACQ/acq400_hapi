#!/usr/bin/env python3

""" host_demux.py Demux Data on HOST Computer
  - data is stored locally, either from mgtdram, ftp or fiber-optic AFHBA404
  - channelize the data
  - optionally store file-per-channel
  - optionally plot in pykst if available
  - @@todo store to MDSplus as segments.

example usage::

    ./host_demux.py --save=DATA --nchan=33 --nblks=-1 --pchan=none acq1102_072,acq1001_073
        # load all blocks, save per channel to subdirectory DATA/data_CC.dat

    ./host_demux.py --nchan=33 --nblks=4 --pchan=1:8 acq1102_072 acq1001_073
        # plot channels 1:8 for both UUTs overlaid on a single figure

    ./host_demux.py --nchan=33 --pchan=3,33 --src=../acq400_chapi/nec14_data acq1102_072
        # plot channels 3 and 33 for 33-channel capture
"""

import numpy as np
import os
import re
import argparse
import subprocess
import copy
import acq400_hapi
import acq400_hapi.channel_handlers as CH
import time
import matplotlib
import matplotlib.pyplot as plt
import logging

if os.getenv('HAPI_MATPLOTLIB') is not None:
    matplotlib.use(os.getenv('HAPI_MATPLOTLIB'))

has_pykst = False
if os.name != "nt":
    try:
        import pykst
        has_pykst = True
        print("INFO: pykst selected as default plot")
    except ImportError:
        pass

logging.getLogger('matplotlib.font_manager').disabled = True

def channel_required(args, ch):
    return args.save != None or args.double_up or ch in list(pc.ic for pc in args.pc_list)

def create_npdata(args, nblk, nchn):
    channels = []
    # Ensure buffer length calculation does not truncate to 0 on fractional nblk
    num_samples = max(1, int(round(nblk * args.NSAM)))

    for counter in range(nchn):
        if channel_required(args, counter):
            channels.append(np.zeros(num_samples, dtype=args.np_data_type))
        else:
            channels.append(np.zeros(16, dtype=args.np_data_type))
    return channels

def make_cycle_list(args):
    if args.cycle == None:
        cyclist = os.listdir(args.uutroot)
        cyclist.sort()
        return cyclist
    else:
        rng = args.cycle.split(':')
        if len(rng) > 1:
            cyclist = [ '{:06d}'.format(c) for c in range(int(rng[0]), int(rng[1])+1) ]
        elif len(args.cycle) == 6:
            cyclist = [ args.cycle ]
        else:
            cyclist = [ '{:06d}'.format(int(args.cycle)) ]

        return cyclist

def get_file_names(args):
    fnlist = list()
    # Matches block numbers (0000, 0.01), .dat files, AND .raw files
    datapat = re.compile(r'([.0-9]{4,5}$|\.dat$|\.raw$)')
    has_cycles = True
    for cycle in make_cycle_list(args):
        if cycle == "err.log":
            continue
        try:
            uutroot = r'{}/{}'.format(args.uutroot, cycle)
            ls = os.listdir(uutroot)
        except:
            uutroot = args.uutroot
            ls = os.listdir(uutroot)
            has_cycles = False

        ls.sort()
        for n, file in enumerate(ls):
            full_path = r'{}/{}'.format(uutroot, file)
            if datapat.search(file) and args.uut in file:
                fnlist.append(full_path)
            elif datapat.search(file) and not os.path.isdir(full_path):
                fnlist.append(full_path)
            else:
                print("no match {}".format(file))
        if not has_cycles:
            break

    return fnlist

def read_data(args, NCHAN):
    data_files = get_file_names(args)
    for n, f in enumerate(data_files):
        print(f)

    NBLK = len(data_files)
    if args.nblks > 0 and NBLK > args.nblks:
        NBLK = args.nblks
        data_files = [ data_files[i] for i in range(0, NBLK) ]

    # Fix: Only group by 3 if we have at least 3 blocks to process
    if NCHAN % 3 == 0 and NBLK >= 3:
        print("collect in groups of 3 to keep alignment")
        GROUP = 3
    else:
        GROUP = 1

    if args.NSAM == 0:
        file_bytes = os.path.getsize(data_files[0])
        # Calculate max whole frames available in file
        total_samples_per_chan = file_bytes // (args.WSIZE * NCHAN)
        args.NSAM = total_samples_per_chan * GROUP
        print("NSAM set {}".format(args.NSAM))

    print("NBLK {} NBLK/GROUP {} NCHAN {}".format(NBLK, NBLK/GROUP, NCHAN))

    effective_nblk = max(1, NBLK / GROUP)
    raw_channels = create_npdata(args, effective_nblk, NCHAN)

    blocks = 0
    i0 = 0
    iblock = 0
    for blknum, blkfile in enumerate(data_files):
        if blocks >= NBLK:
            break
        if blkfile != "analysis.py" and blkfile != "root":
            if blknum == 0:
                args.src = blkfile

            # Read whole sample frames only (trims truncated partial frame bytes at end)
            raw_bytes = os.path.getsize(blkfile)
            valid_samples = (raw_bytes // (args.WSIZE * NCHAN)) * NCHAN
            file_data = np.fromfile(blkfile, dtype=args.np_data_type, count=valid_samples)

            if iblock == 0:
                data = file_data
            else:
                data = np.append(data, file_data)

            iblock += 1
            if iblock < GROUP:
                continue

            samples_read = len(data) // NCHAN
            i1 = i0 + samples_read

            for ch in range(NCHAN):
                if channel_required(args, ch):
                    raw_channels[ch][i0:i1] = data[ch::NCHAN]

            i0 = i1
            blocks += 1
            iblock = 0

    args.src = "{}..{}".format(args.src, os.path.basename(blkfile))

    print("length of data = ", len(raw_channels))
    return raw_channels

def read_data_file(args, NCHAN):
    raw_bytes = os.path.getsize(args.src)
    valid_samples = (raw_bytes // (args.WSIZE * NCHAN)) * NCHAN
    data = np.fromfile(args.src, dtype=args.np_data_type, count=valid_samples)

    nsam = len(data) // NCHAN
    args.NSAM = nsam
    raw_channels = create_npdata(args, 1, NCHAN)

    for ch in range(NCHAN):
        if channel_required(args, ch):
            raw_channels[ch] = data[ch::NCHAN]
    return raw_channels

def save_dirfile(args, raw_channels):
    uutname = args.uut
    for ch0, channel in enumerate(raw_channels):
        ch1 = ch0+1
        if args.schan:
            if ch1 not in args.schan:
                continue
        data_file = open("{}/{}_{:02d}.dat".format(args.saveroot, uutname, ch1), "wb+")
        channel.tofile(data_file, '')

    print("data saved to directory: {}".format(args.saveroot))
    with open("{}/format".format(args.saveroot), 'w') as fmt:
        fmt.write("# dirfile format file for {}\n".format(uutname))
        for enum, channel in enumerate(raw_channels):
            fmt.write("{}_{:02d}.dat RAW s 1\n".format(uutname, enum+1))

def save_numpy(args, raw_channels):
    npfile = "{}/{}.npy".format(args.saveroot, args.uut)
    cooked = cook_data(args, raw_channels)
    print("save_numpy {}  {}".format(npfile, cooked))
    np.save(npfile, cooked)

def save_data(args, raw_channels):
    if os.name == "nt": 
        path = r'{}:\\demuxed\{}'.format(args.drive_letter, args.uut)
        if not os.path.exists(path):
            os.makedirs(path)
        args.saveroot = path
    else:
        subprocess.call(["mkdir", "-p", args.saveroot])

    if args.save == 'npy':
        save_numpy(args, raw_channels)
    else:
        save_dirfile(args, raw_channels)

    return raw_channels

def plot_mpl_combined(uut_data_list):
    """ Plot combined channels from multiple UUTs onto a single figure """
    if not uut_data_list:
        return

    _, _, first_args = uut_data_list[0]
    
    nplot = len(first_args.pc_list)
    total_plots = int(nplot / first_args.traces_per_plot)
    if nplot % first_args.traces_per_plot:
        total_plots += 1

    if total_plots > 1:
        fig, plots = plt.subplots(total_plots, 1, sharex=True)
    else:
        fig, p1 = plt.subplots()
        plots = (p1,)

    uut_names_str = ", ".join([u[0] for u in uut_data_list])
    fig.suptitle("UUTs: {}\n{}".format(uut_names_str, first_args.pcfg if first_args.pcfg else ''))

    xl = "Samples"
    for pln, ch_handler in enumerate(first_args.pc_list):
        plot_idx = int(pln / first_args.traces_per_plot)

        for uut_name, raw_channels, args in uut_data_list:
            yy, meta, not_smooth = ch_handler(raw_channels, args.pses)
            
            start, end, stride = args.pses
            if args.egu >= 1:
                x1 = start
                x2 = x1 + (len(yy) - 1) * stride
                if args.xdt == 0:
                    ti = 1/float(args.the_uut.s0.SIG_CLK_S1_FREQ.split(" ")[-1])
                else:
                    ti = args.xdt
                xx = np.linspace(x1*ti, x2*ti, len(yy))
                xl = "seconds"
            else:
                xx = np.array([start + x*stride for x in range(len(yy))])
                xl = "Samples"

            meta_parts = meta.split(' ')
            if len(meta_parts) > 1:
                plots[plot_idx].set_ylabel(meta_parts[1])
            plots[plot_idx].set_title("Channel {}".format(meta_parts[0]))

            label_name = f"{uut_name}"
            if not_smooth:
                plots[plot_idx].step(xx, yy, linewidth=0.75, label=label_name)
            else:
                plots[plot_idx].plot(xx, yy, linewidth=0.75, label=label_name)

        plots[plot_idx].grid(True, linewidth=0.2)
        plots[plot_idx].ticklabel_format(style='plain')
        plots[plot_idx].legend(loc="upper right", fontsize="small")

    plots[-1].set_xlabel(xl)
    plt.subplots_adjust(hspace=(total_plots - 1) * 0.15)

    if first_args.custom_string:
        fig = plt.gcf()
        fig.set_size_inches(16, 9)
        plt.savefig(f"combined_{first_args.custom_string}.pdf", format='pdf', bbox_inches='tight')
    else:
        plt.show()

def process_cmdline_cfg(args):
    print_ic = [ int(i)-1 for i in make_pc_list(args)]
    pl = ()
    if args.egu >= 1:
        pl = list(CH.ch_egu(ic, args) for ic in print_ic)
    else:
        pl = list(CH.ch_raw(ic) for ic in print_ic)

    if args.tai_vernier:
        pl = pl.extend(CH.ch_tai_vernier(args.tai_vernier-1))

    return pl

def plot_data_kst(args, raw_channels):
    client = pykst.Client("NumpyVector")
    llen = len(raw_channels[0])
    if args.egu >= 1:
        if args.xdt == 0:
            if args.egu == 1:
                print("WARNING ##### NO CLOCK RATE PROVIDED. TIME SCALE measured by system.")
                raw_input("Please press enter if you want to continue with inaccurate time base.")
            time1 = float(args.the_uut.s0.SIG_CLK_S1_FREQ.split(" ")[-1])
            xdata = np.linspace(0, llen/time1, num=llen)
        else:
            xdata = np.linspace(0, llen*args.xdt, num=llen)
        xname= 'time'
        yu = 'V'
        xu = 's'
    else:
        xname = 'idx'
        yu = 'code'
        xu = 'sample'
        xdata = np.arange(0, llen).astype(np.float64)

    V1 = client.new_editable_vector(xdata, name=xname)

    for ch in [ int(c) for c in args.pc_list]:
        channel = raw_channels[ch]
        ch1 = ch+1
        yu1 = yu
        if args.egu:
            try:
                channel = args.the_uut.chan2volts(ch1, channel)
            except IndexError:
                yu1 = 'code'
                print("ERROR: no calibration for CH{:02d}".format(ch1))

        V2 = client.new_editable_vector(channel.astype(np.float64), name="{}:CH{:02d}".format(re.sub(r"_", r"-", args.uut), ch1))
        c1 = client.new_curve(V1, V2)
        p1 = client.new_plot()
        p1.set_left_label(yu1)
        p1.set_bottom_label(xu)
        p1.add(c1)

def double_up(args, d1):
    d2 = []
    for ch in range(args.nchan):
        ch2 = ch * 2
        ll = d1[ch2]
        rr = d1[ch2+1]
        mm = np.column_stack((ll, rr))
        mm1 = np.reshape(mm, (len(ll)*2, 1))
        d2.append(mm1)

    return d2

def stack_480_shuffle(args, raw_data):
    r2 = []
    for i1 in args.stack_480_cmap:
        r2.append(raw_data[i1])

    return r2

def cook_data(args, raw_channels):
    clidata = {}
    for num, ch_handler in enumerate(args.pc_list):
        yy, ylabel, step = ch_handler(raw_channels, args.pses)
        clidata[ylabel] = yy

    return clidata

def map_from_embedded_cmap(args, raw_data):
    try:
        cmap = [ int(ch0) for ch0 in args.the_uut.s0.channel_mapping.split(',') ]
        print(cmap)

        r2 = []
        for i1 in cmap:
            r2.append(raw_data[i1])
        return r2
    except:
        print("WARNING: channel_mapping request failed (old firmware?), use 1:1")
        return raw_data

def process_data(args):
    NCHAN = args.nchan
    if args.double_up:
        NCHAN = args.nchan * 2
        print("nchan = ", args.nchan)

    raw_data = read_data(args, NCHAN) if not os.path.isfile(args.src) else read_data_file(args, NCHAN)

    if args.cmap:
        raw_data = map_from_embedded_cmap(args, raw_data)
    if args.double_up:
        raw_data = double_up(args, raw_data)

    if args.stack_480:
        raw_data = stack_480_shuffle(args, raw_data)

    if args.callback:
        args.callback(cook_data(args, raw_data))

    if args.save != None:
        save_data(args, raw_data)

    return raw_data

def make_pc_list(args):
    if args.pchan == 'none':
        return list()
    if args.pchan == 'all':
        return list(range(1,args.nchan+1))
    elif len(args.pchan.split(':')) > 1:
        lr = args.pchan.split(':')
        x1 = 1 if lr[0] == '' else int(lr[0])
        x2 = args.nchan+1 if lr[1] == '' else int(lr[1])+1
        return list(range(x1, x2))
    else:
        return args.pchan.split(',')

def calc_stack_480(args):
    args.double_up = 0
    if not args.stack_480:
        return
    if args.stack_480 == '2x4':
        args.stack_480_cmap = ( 0, 1, 4, 5, 2, 3, 6, 7 )
        args.double_up = 1
        args.nchan = 8
    elif args.stack_480 == '2x8':
        args.nchan = 16
        args.stack_480_cmap = (
            0,  1,  2,  3,  8,  9, 10, 11,  4,  5,  6,  7, 12, 13, 14, 15 )
    elif args.stack_480 == '4x8':
        args.nchan = 32
        args.stack_480_cmap = (
            0,  1,  2,  3,  8,  9, 10, 11,  4,  5,  6,  7, 12, 13, 14, 15,
           16, 17, 18, 19, 24, 25, 26, 27, 20, 21, 22, 23, 28, 29, 30, 31 )
    elif args.stack_480 == '6x8':
        args.nchan = 48
        args.stack_480_cmap = (
            0,  1,  2,  3,  8,  9, 10, 11,  4,  5,  6,  7, 12, 13, 14, 15,
           16, 17, 18, 19, 24, 25, 26, 27, 20, 21, 22, 23, 28, 29, 30, 31,
           32, 33, 34, 35, 40, 41, 42, 43, 36, 37, 38, 39, 44, 45, 46, 47 )
    else:
        print("bad option {}".format(args.stack_480))
        quit()

    print("args.stack_480_cmap: {}".format(args.stack_480_cmap))

def getRootFromAfhba404(args):
    for conn in acq400_hapi.afhba404.get_connections().values():
        if conn.uut == args.uut:
            return f'/mnt/afhba.{conn.dev}/{args.uut}'

    print(f'getRootFromAhfba404 ERROR no connection for {args.uut}')
    exit(1)

def run_main(args):
    uut_list = [uut for uut_arg in args.uuts for uut in uut_arg.split(',') if uut]
    collected_uut_data = []

    for uut_name in uut_list:
        uut_args = copy.copy(args)
        uut_args.uut = uut_name

        if uut_args.double_up == 0:
            calc_stack_480(uut_args)
        uut_args.WSIZE = 2
        uut_args.NSAM = 0

        if uut_args.data_type == None or uut_args.nchan == None or uut_args.egu == 1:
            try:
                uut_args.the_uut = acq400_hapi.factory(uut_args.uut)
            except:
                print(f'ERROR: unable to instantiate UUT {uut_args.uut}')
                print("maybe it's not there and we wouldn't need if --data_type, --nchan are defined and egu=0")
                exit(1)

        if uut_args.data_type == None:
            uut_args.data_type = 32 if int(uut_args.the_uut.s0.data32) else 16
        if uut_args.nchan == None:
            uut_args.nchan = int(uut_args.the_uut.s0.NCHAN)

        if uut_args.data_type == 16:
            uut_args.np_data_type = np.int16
            uut_args.WSIZE = 2
        elif uut_args.data_type == 8:
            uut_args.np_data_type = np.int8
            uut_args.WSIZE = 1
        else:
            uut_args.np_data_type = np.int32
            uut_args.WSIZE = 4

        print("Processing UUT: {} | data_type {} np {}".format(uut_args.uut, uut_args.data_type, uut_args.np_data_type))
        if uut_args.src == "@afhba404":
            uut_args.uutroot = getRootFromAfhba404(uut_args)
            print(f'found uutroot for {uut_args.uut} on  {uut_args.uutroot}')
        elif os.name == "nt":  
            uut_args.src  = uut_args.src.replace("/","\\")
            if os.path.isdir(uut_args.src):
                uut_args.uutroot = uut_args.src
            elif os.path.isfile(uut_args.src):
                uut_args.uutroot = os.path.dirname(uut_args.src)
            else:
                print(f'Error: unable to locate data, src {uut_args.src}')
                exit(1)
        elif os.path.isdir(uut_args.src):
            uut_args.uutroot = os.path.join(uut_args.src, uut_args.uut)
            if not os.path.isdir(uut_args.uutroot):
                uut_args.uutroot = uut_args.src
        elif os.path.isfile(uut_args.src):
            uut_args.uutroot = os.path.dirname(uut_args.src)
        else:
            print(f'Error: unable to locate data, src {uut_args.src}')
            exit(1)

        if uut_args.save != None:
            path_prefixes = ('/', './', '../')
            if uut_args.save.startswith(path_prefixes):
                uut_args.saveroot = uut_args.save
            else:
                if os.name != "nt":
                    uut_args.saveroot = r"{}/{}".format(uut_args.uutroot, uut_args.save)

        if uut_args.pcfg:
            uut_args.pc_list = CH.process_pcfg(uut_args)
        else:
            uut_args.pc_list = process_cmdline_cfg(uut_args)

        raw_channels = process_data(uut_args)
        collected_uut_data.append((uut_name, raw_channels, uut_args))

    if args.plot and collected_uut_data:
        if has_pykst:
            for uut_name, raw_channels, uut_args in collected_uut_data:
                plot_data_kst(uut_args, raw_channels)
        else:
            plot_mpl_combined(collected_uut_data)

def list_of_ints(string):
    return list(map(int, string.split(',')))

def get_parser(parser=None):
    if not parser:
        is_client = True
        parser = argparse.ArgumentParser(description='Host side data demuxing and plotting')
    else:
        is_client = False
    parser.add_argument('--nchan', type=int, default=None)
    parser.add_argument('--nblks', type=int, default=-1)
    parser.add_argument('--save', type=str, default=None, help='save channelized data to dir')
    parser.add_argument('--src', type=str, default='/data', help='data source root')
    parser.add_argument('--cycle', type=str, default=None, help='cycle from rtm-t-stream-disk')
    parser.add_argument('--pchan', type=str, default=':', help='channels to plot')
    parser.add_argument('--pses', type=acq400_hapi.ArgTypes.start_end_stride, default=(0, -1, 1), help="plot start:end:stride, default: 0:-1:1")
    parser.add_argument('--tai_vernier', type=int, default=None, help='decode this channel as tai_vernier')
    parser.add_argument('--egu', type=int, default=0, help='>0 plot egu (V vs s) >1 : used computed s')
    parser.add_argument('--xdt', type=eval, default=0, help='0: use interval from UUT, else specify interval ')
    parser.add_argument('--data_type', type=int, default=None, help='Use int16 or int32 for data demux.')
    parser.add_argument('--double_up', type=int, default=0, help='Use for ACQ480 two lines per channel mode')
    parser.add_argument('--plot_mpl', type=int, default=0, help='Use MatPlotLib to plot subrate data. (legacy option)')
    parser.add_argument('--plot', type=int, default=1, help="plot data when set")
    parser.add_argument('--stack_480', type=str, default=None, help='Stack : 2x4, 2x8, 4x8, 6x8')
    parser.add_argument('--drive_letter', type=str, default="D", help="Which drive letter to use when on windows.")
    parser.add_argument('--pcfg', default=None, type=str, help="plot configuration file, overrides pchan")
    parser.add_argument('--callback', default=None, help="callback for external automation")
    parser.add_argument('--traces_per_plot', default=1, type=int, help="traces_per_plot")
    parser.add_argument('--schan', default=None, type=list_of_ints, help="channels to save ie 1,49,50")
    parser.add_argument('--cmap', default=1, type=int, help="use embedded channel mapping")
    parser.add_argument('--custom_string', default=None, help="custom string for saved PNG filename")
    if is_client:
        parser.add_argument('uuts', nargs='+', help='uut - for auto configuration data_type, nchan, egu or just a label')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
