#!/usr/bin/env python

"""
A python script to demux the data from the cs system.

The data is supposed to come out in the following way:

CH01 .. CH02 .. CH03 .. CH04 .. INDEX .. FACET .. SAM COUNT .. usec COUNT
short   short   short   short   long     long     long          long

Usage:
Linux:
python cs_demux.py --data_file="/home/sean/PROJECTS/workspace/acq400_hapi-1/user_apps/
                                    acq400/acq1001_068/000001/0000"
Windows:
python .\cs_demux.py --plot_facets=4 --data_file="C:/acq2106_112/000001/0000"
"""


import numpy as np
import matplotlib.pyplot as plt
import argparse



# Sample in u32
# <ACQ420    ><QEN         ><AGG        >
# <AI12><AI34><FACET><INDEX><AGSAM><USEC>

# msb_direct: msb of FACET, INDEX is an embedded digital value


LPS = 6       # longs per sample
ESS = 4       # EVENT signature length in samples
ESL = LPS*ESS # ES length in LW
SPS = LPS*2   # shorts per sample

# function offsets in longs
IX_AI0102 = 0 
IX_AI0304 = 1
IX_FACET  = 2
IX_INDEX  = 3
IX_AGSAM  = 4
IX_USEC   = 5

# logical channel offsets

CH_AI01 = 0
CH_AI02 = 1
CH_AI03 = 2
CH_AI04 = 3
CH_FACET = 4
CH_INDEX = 5
CH_AGSAM = 6
CH_USEC = 7
CH_DI2  = 8
CH_DI4  = 9

PREV_INDEX = LPS-IX_INDEX   # look back to INDEX in previous sample
NEXT_INDEX = ESL+IX_INDEX   # look forward to next INDEX from beginning of ES

def isES(d):
    return d[0] == 0xaa55f154 and d[1] == 0xaa55f154 and d[2] == 0xaa55f15f and d[3] == 0xaa55f15f

def find_zero_index(args):
    # This function finds the first 0xaa55f154 short value in the data and then
    # uses its position to check the index before this event sample and the
    # index after this event sample and checks the latter is one greater
    # than the former. If the values do not increment then go to the next
    # event sample and repeat.

    for pos, lvnu in enumerate(args.data32):
        if isES(args.data32[pos:pos+ESL]):
            # Check current index
            first_es_position = pos
            break

    print("DEBUG: first_es_position {}".format(first_es_position))
    # loop over all the event samples. Look at the "index" value before and
    # after and check they have incremented.
    next_es = args.transient_length*LPS + ESL
    
    for pos, lvnu in enumerate(args.data32[first_es_position:]):
        if pos > 0 and pos % next_es == 0:
            if not isES(args.data32[pos:pos+ESL]):
                print("ERROR: expected ES at {}".format(pos))
                exit(1)
            print("DEBUG: counter {} samples {}".format(pos, pos//LPS))            
            if args.isNewIndex(args.data32[pos - PREV_INDEX], args.data32[pos + NEXT_INDEX]):
                return pos

    print("ERROR: we do not want to be here")
    exit(1)


def extract_bursts(args, zero_index):
    burst32 = args.transient_length*LPS
    burst16 = args.transient_length*SPS
    burst_es = args.transient_length*LPS + ESL
    data = []

    print("extract_bursts() {}, {}, {}".format(zero_index+ESL, len(args.data32), burst_es))
    first_time = True
    for bxx in range(zero_index+ESL, len(args.data32), burst_es):        
        b32 = bxx + 2       # skip AI
        b16 = bxx * 2       # scale to data16
        if first_time:
            for ic in range(0, 4):
                data.append(args.data16[b16:b16+burst16:SPS])
                b16 += 1
            for ic in range(0, 4):
                data.append(args.data32[b32:b32+burst32:LPS])
                b32 +=1
            #print(data)
            first_time = False
        else:
            for ic in range(0, 4):
                data[ic] = np.concatenate((data[ic], args.data16[b16:b16+burst16:SPS]))
                b16 += 1
            for ic in range(0, 4):
                data[ic+4] = np.concatenate((data[ic+4], args.data32[b32:b32+burst32:LPS]))
                b32 +=1
    
    if args.msb_direct:
        tmp = np.bitwise_and(data[CH_FACET], 0x80000000)
        data.append(np.logical_and(tmp, tmp))
        tmp = np.bitwise_and(data[CH_INDEX], 0x80000000)
        data.append(np.logical_and(tmp, tmp))
        
        data[4] = np.bitwise_and(data[CH_FACET], 0x7fffffff)        
        data[5] = np.bitwise_and(data[CH_INDEX], 0x7fffffff)
         
    for ic, ch in enumerate(data):
        print("{} {}".format(ic, ch.shape))
    return data
        
def save_data(args, data):
    np.tofile("test_file", data)
    return None


def get_plot_timebase(args, data):
    maxlen = min([len(d) for d in data])
 
    if args.plot_facets != -1:
        plen = args.transient_length*args.plot_facets
        if plen > maxlen:
            plen = maxlen
    else:
        plen = maxlen
    tt = range(0, plen)
    return plen, tt 
   
def plot_data(args, data):
    axes = [
        "Demuxed channels from acq1001" + (" rev2 with embedded D1,D2" if args.msb_direct else "") + "\nfile:{}".format(args.data_file),
        "CH01 \n (Sampled \n FACET)",
        "CH02 \n (Sampled \n INDEX)",
        "CH03 \n (Sampled \n Sine Wave)",
        "CH04 \n (Sampled \n D2)",
        "FACET \n (u32)",
        "INDEX \n (u32)",
        "Sample Count\n (u32)",
        "usec Count\n (u32)",
        "D1\n (bool)",
        "D2\n (bool)"    
    ]

    nsp = 8 if not args.msb_direct else 10    
    plen, tt = get_plot_timebase(args, data)
          
    for sp in range(0,nsp):        
        if sp == 0:
            ax0 = plt.subplot(nsp,1,sp+1)
            ax0.set_title(axes[0])
            ax = ax0
        else:
            ax = plt.subplot(nsp,1,sp+1, sharex=ax0)
        lastplot = sp == nsp-1
            
        ax.set_ylabel(axes[sp+1])                  
        plt.plot(tt, data[sp][:plen])
        plt.tick_params('x', labelbottom=lastplot)
 

    ax.set_xlabel("Samples")
    plt.show()
    return None

def isNewIndex_default(w1, w2):
    return w1+1 == w2

def isNewIndex_msb_direct(w1, w2):
    return (w1&0x7fffffff)+1 == (w2&0x7fffffff)

def run_main():
    parser = argparse.ArgumentParser(description='cs demux')
    parser.add_argument('--plot', default=1, type=int, help="Plot data")
    parser.add_argument('--plot_facets', default=-1, type=int, help="No of facets"
                                                                    "to plot")
    parser.add_argument('--save', default=0, type=int, help="Save data")
    parser.add_argument('--transient_length', default=8192, type=int, help='transient length')
    parser.add_argument("--data_file", default="./shot_data", type=str, help="Name of"
                                                                    "data file")
    parser.add_argument("--msb_direct", default=0, type=int, help="new msb_direct feature, d2/d4 embedded in count d31")
    args = parser.parse_args()
    args.isNewIndex = isNewIndex_msb_direct if args.msb_direct else isNewIndex_default
    
    args.data32 = np.fromfile(args.data_file, dtype=np.uint32)
    args.data16 = np.fromfile(args.data_file, dtype=np.int16)

    data = extract_bursts(args, find_zero_index(args))
    if args.plot == 1:
            plot_data(args, data)
    if args.save == 1:
        save_data(args, data)

if __name__ == '__main__':
    run_main()
