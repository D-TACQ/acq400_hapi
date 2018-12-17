#!/usr/bin/env python

""" host_demux.py Demux Data on HOST Computer

  - data is stored locally, either from mgtdram/ftp or fiber-optic AFHBA404
  - channelize the data
  - optionally store file-per-channel
  - optionally plot in pykst
  - @@todo store to MDSplus as segments.

example usage::

    ./host_demux.py --save=DATA --nchan=32 --nblks=-1 --pchan=none acq2106_067
        # load all blocks, save per channel to subdirectory DATA/data_CC.dat

    ./host_demux.py --nchan=32 --nblks=4 --pchan=1:8 acq2106_067
        # plot channels 1:8, 4 blocks


    ./host_demux.py --nchan=32 --nblks=-1 --pchan=1,2 acq2106_067
        # plot channels 1,2, ALL blocks
        # works for 8GB data, best to LIMIT the number of channels ..

    ./host_demux.py --nchan=96 --src=/data/ACQ400DATA/1 \
        --egu=1 --xdt=2e-6 --cycle=1:4 --pchan=1:2 \
        acq2106_061
        # plot AFHBA404 data from PORT1
        # plot egu (V vs s), specify interval, plot 4 cycles, plot 2 channels
        # uut

    use of --src
        --src=/data                     # valid for FTP upload data
        --src=/data/ACQ400DATA/1 	# valid for SFP data, port 1
        --src=afhba.0.log               # one big raw file, eg from LLC

    ./host_demux.py --nchan 128 --pchan 1,33,65,97 --src=/path-to/afhba.0.log acq2106_110
    # plot data from LLC, 128 channels, show one "channel" from each site.
    # 97 was actually the LSB of TLATCH.

usage::

    host_demux.py [-h] [--nchan NCHAN] [--nblks NBLKS] [--save SAVE]
                     [--src SRC] [--pchan PCHAN]
                     uut

host demux, host side data handling

positional arguments:
  uut            uut

optional arguments:
  -h, --help     show this help message and exit
  --nchan NCHAN
  --nblks NBLKS
  --save SAVE    save channelized data to dir
  --src SRC      data source root
  --pchan PCHAN  channels to plot
  --egu EGU      plot egu (V vs s)
  --xdt XDT      0: use interval from UUT, else specify interval
  --double_up    Use for ACQ480 two lines per channel mode

if --src is a file, use it directly
    dir/nnnn
if --src is a directory, first check if it has cycles:
    dir/NNNNN/nnnnn*
else iterate files in dir
    dir/nnnnn*

TO DEMUX ON WINDOWS TO STORE CHANNELISED DATA:
python .\host_demux.py --save=1 --src="[dir]" --pchan=none acq2106_114
    Make sure that the muxed data is in D:\\[dir]\[UUT name]\
Where [dir] is the location of the data.

Demuxed data will be written to D:\\demuxed\[UUT name]\
To plot subsampled data on windows:

python .\host_demux.py --src=Projects --nchan=8
--pchan 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 --stack_480="2x8" --plot_mpl=1 acq2106_120

"""


import numpy as np
import os
import re
import argparse
import subprocess
import acq400_hapi
import time
import matplotlib.pyplot as plt

has_pykst = False
if os.name != "nt":
    try:
        import pykst
        has_pykst = True
    except ImportError:
        print("WARNING: failed to import pykst, no kst plots")


def channel_required(args, ch):
#    print("channel_required {} {}".format(ch, 'in' if ch in args.pc_list else 'out', args.pc_list))
    return args.save != None or args.double_up or ch in args.pc_list

def create_npdata(args, nblk, nchn):
    channels = []

    for counter in range(nchn):
       if channel_required(args, counter):
           channels.append(np.zeros((nblk*args.NSAM), dtype=args.np_data_type))

       else:
           channels.append(np.zeros(16, dtype=args.np_data_type))
    # print "length of data = ", len(total_data)
    # print "npdata = ", npdata
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
# matches BOTH 0.?? for AFHBA an 0000 for FTP
    datapat = re.compile('[.0-9]{4}$')
    has_cycles = True
    for cycle in make_cycle_list(args):
        if cycle == "err.log":
            continue
        try:
            uutroot = r'{}/{}'.format(args.uutroot, cycle)
            print("debug")
            ls = os.listdir(uutroot)
            print("uutroot = ", uutroot)
        except:
            uutroot = args.uutroot
            ls = os.listdir(uutroot)
            has_cycles = False

        ls.sort()
        for n, file in enumerate(ls):
            if datapat.match(file):
                fnlist.append(r'{}/{}'.format(uutroot, file) )
            else:
                print("no match {}".format(file))
        if not has_cycles:
            break

    return fnlist

def read_data(args, NCHAN):
    # global NSAM
    data_files = get_file_names(args)
    for n, f in enumerate(data_files):
        print(f)
    if NCHAN % 3 == 0:
        print("collect in groups of 3 to keep alignment")
        GROUP = 3
    else:
        GROUP = 1


    if args.NSAM == 0:
        args.NSAM = GROUP*os.path.getsize(data_files[0])/args.WSIZE/NCHAN
        print("NSAM set {}".format(args.NSAM))

    NBLK = len(data_files)
    if args.nblks > 0 and NBLK > args.nblks:
        NBLK = args.nblks
        data_files = [ data_files[i] for i in range(0,NBLK) ]

    print("NBLK {} NBLK/GROUP {} NCHAN {}".format(NBLK, NBLK/GROUP, NCHAN))

    raw_channels = create_npdata(args, NBLK/GROUP, NCHAN)
    blocks = 0
    i0 = 0
    iblock = 0
    for blknum, blkfile in enumerate(data_files):
        if blocks >= NBLK:
            break
        if blkfile != "analysis.py" and blkfile != "root":

            print blkfile, blknum
            # concatenate 3 blocks to ensure modulo 3 channel align
            if iblock == 0:
                data = np.fromfile(blkfile, dtype=args.np_data_type)
            else:
                data = np.append(data, np.fromfile(blkfile, dtype=args.np_data_type))



            iblock += 1
            if iblock < GROUP:
                continue

            i1 = i0 + args.NSAM
            for ch in range(NCHAN):
                if channel_required(args, ch):
                    raw_channels[ch][i0:i1] = (data[ch::NCHAN])
                # print x
            i0 = i1
            blocks += 1
            iblock = 0

    print "length of data = ", len(raw_channels)
    print "length of data[0] = ", len(raw_channels[0])
    print "length of data[1] = ", len(raw_channels[1])
    return raw_channels

def read_data_file(args, NCHAN):
    # NCHAN = args.nchan
    data = np.fromfile(args.src, dtype=args.np_data_type)

    nsam = len(data)/NCHAN
    raw_channels = create_npdata(args, nsam, NCHAN)
    for ch in range(NCHAN):
        if channel_required(args, ch):
            raw_channels[ch] = data[ch::NCHAN]

    return raw_channels

def save_data(args, raw_channels):

    if os.name == "nt": # if system is windows.
        path = r'{}:\\demuxed\{}'.format(args.drive_letter, args.uut[0]) # raw string literal so we can use \ in path.
        if not os.path.exists(path):
            os.makedirs(path)
        args.saveroot = path # set args.saveroot to windows style dir.

    else:
        subprocess.call(["mkdir", "-p", args.saveroot])

    uutname = args.uut[0]
    for enum, channel in enumerate(raw_channels):
        data_file = open("{}/{}_{:02d}.dat".format(args.saveroot, uutname, enum+1), "wb+")
        channel.tofile(data_file, '')

    print "data saved to directory: {}".format(args.saveroot)
    with open("{}/format".format(args.saveroot), 'w') as fmt:
        fmt.write("# dirfile format file for {}\n".format(uutname))
        for enum, channel in enumerate(raw_channels):
            fmt.write("{}_{:02d}.dat RAW s 1\n".format(uutname, enum+1))

    return raw_channels


def plot_mpl(args, raw_channels):
    print "Plotting with MatPlotLib. Subrate = {}".format(args.mpl_subrate)
    #real_len = len(raw_channels[0]) # this is the real length of the channel data
    num_of_ch = len(args.pc_list)
    f, plots = plt.subplots(num_of_ch, 1)
    for num, sp in enumerate(args.pc_list):
        plots[num].plot(raw_channels[sp][args.mpl_start:args.mpl_end:args.mpl_subrate])
    plt.show()
    return None


def plot_data_kst(args, raw_channels):
    client = pykst.Client("NumpyVector")
    llen = len(raw_channels[0])
    if args.egu == 1:
        if args.xdt == 0:
            print "WARNING ##### NO CLOCK RATE PROVIDED. TIME SCALE measured by system."
            raw_input("Please press enter if you want to continue with innacurate time base.")
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
            # chan2volts ch index from 1:
                channel = args.the_uut.chan2volts(ch1, channel)
            except IndexError:
                yu1 = 'code'
                print("ERROR: no calibration for CH{:02d}".format(ch1))

        # label 1.. (human)
        V2 = client.new_editable_vector(channel.astype(np.float64), name="{}:CH{:02d}".format(re.sub(r"_", r"-", args.uut[0]), ch1))
        c1 = client.new_curve(V1, V2)
        p1 = client.new_plot()
        p1.set_left_label(yu1)
        p1.set_bottom_label(xu)
        p1.add(c1)


def plot_data(args, raw_channels):
    if args.plot_mpl == 1:
        # if arg set then plot with matplotlib instead.
        plot_mpl(args, raw_channels)
        return None

    if has_pykst:
        plot_data_kst(args, raw_channels)
    else:
        print("SORRY, kst automation via pykst not available. Please install pykst, or use kst DirFile importer")

# double_up : data is presented as [ ch010, ch011, ch020, ch021 ] .. so zip them together..
def double_up(args, d1):
    d2 = []
    for ch in range(args.nchan):
        ch2 = ch * 2
        ll = d1[ch2]
        #print ll.shape
        rr = d1[ch2+1]
        #print rr.shape
        mm = np.column_stack((ll, rr))
	#print mm.shape
        mm1 = np.reshape(mm, (len(ll)*2, 1))
	#print mm1.shape
        d2.append(mm1)

    return d2


def stack_480_shuffle(args, raw_data):
    r2 = []
    for i1 in args.stack_480_cmap:
        r2.append(raw_data[i1])

    return r2


def process_data(args):
    NCHAN = args.nchan
    if args.double_up:
        NCHAN = args.nchan * 2
        print "nchan = ", args.nchan

    raw_data = read_data(args, NCHAN) if not os.path.isfile(args.src) else read_data_file(args, NCHAN)

    if args.double_up:
	       raw_data = double_up(args, raw_data)

    if args.stack_480:
        raw_data = stack_480_shuffle(args, raw_data)

    if args.save != None:
        save_data(args, raw_data)
    if len(args.pc_list) > 0:
        plot_data(args, raw_data)

def make_pc_list(args):
    # ch in 1.. (human)
    if args.pchan == 'none':
        return list()
    if args.pchan == 'all':
        return list(range(0,args.nchan))
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

def run_main():
    parser = argparse.ArgumentParser(description='host demux, host side data handling')
    parser.add_argument('--nchan', type=int, default=32)
    parser.add_argument('--nblks', type=int, default=-1)
    parser.add_argument('--save', type=str, default=None, help='save channelized data to dir')
    parser.add_argument('--src', type=str, default='/data', help='data source root')
    parser.add_argument('--cycle', type=str, default=None, help='cycle from rtm-t-stream-disk')
    parser.add_argument('--pchan', type=str, default=':', help='channels to plot')
    parser.add_argument('--egu', type=int, default=0, help='plot egu (V vs s)')
    parser.add_argument('--xdt', type=float, default=0, help='0: use interval from UUT, else specify interval ')
    parser.add_argument('--data_type', type=int, default=16, help='Use int16 or int32 for data demux.')
    parser.add_argument('--double_up', type=int, default=0, help='Use for ACQ480 two lines per channel mode')
    parser.add_argument('--plot_mpl', type=int, default=0, help='Use MatPlotLib to plot subrate data.')
    parser.add_argument('--mpl_subrate', type=int, default=1000, help='Control subrate for mpl plotting.')
    parser.add_argument('--mpl_start', type=int, default=0, help='Control number of samples to plot with mpl.')
    parser.add_argument('--mpl_end', type=int, default=-1, help='Control number of samples to plot with mpl.')
    parser.add_argument('--stack_480', type=str, default=None, help='Stack : 2x4, 2x8, 4x8, 6x8')
    parser.add_argument('--drive_letter', type=str, default="D", help="Which drive letter to use when on windows.")
    parser.add_argument('uut', nargs=1, help='uut')
    args = parser.parse_args()
    calc_stack_480(args)
    args.WSIZE = 2
    args.NSAM = 0
    if args.data_type == 16:
        args.np_data_type = np.int16
        args.WSIZE = 2
    else:
        args.np_data_type = np.int32
        args.WSIZE = 4

    if os.name == "nt":  # do this if windows system.
        args.uutroot = r"{}:\{}\{}".format(args.drive_letter, args.src, args.uut[0])
    elif os.path.isdir(args.src):
        args.uutroot = r"{}/{}".format(args.src, args.uut[0])
        print("uutroot {}".format(args.uutroot))
    elif os.path.isfile(args.src):
        args.uutroot = "{}".format(os.path.dirname(args.src))
    if args.save != None:
        if args.save.startswith("/"):
            args.saveroot = args.save
        else:
            if os.name != "nt":
                args.saveroot = r"{}/{}".format(args.uutroot, args.save)

    # ch 0.. (comp)
    args.pc_list = [ int(i)-1 for i in make_pc_list(args)]
    print("args.pc_list {}".format(args.pc_list))
    if args.egu:
        args.the_uut = acq400_hapi.Acq2106(args.uut[0])
    process_data(args)

if __name__ == '__main__':
    run_main()

