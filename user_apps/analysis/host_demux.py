import pykst
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
import time
import gc
import re

NSAM = 1048576
NBLK = 16
NCHN = 32

def create_npdata(nblk, nchn):
    channels = []

    for counter in range(nchn):
       channels.append(np.zeros((nblk*NSAM), dtype=np.int16))
    # print "length of data = ", len(total_data)
    # print "npdata = ", npdata
    return channels 


def read_data():
    #print "dir contents: ", listdir("./")
    current_dir_contents = listdir("./")
    data_files = list()

    datapat = re.compile('[0-9]{4}')
    for blknum, blkfile in enumerate(current_dir_contents):
        if datapat.match(blkfile):
            data_files.append(blkfile)

    NBLK = len(data_files)
    print("NBLK {} NCHN {}".format(NBLK, NCHN))
   
    raw_channels = create_npdata(len(data_files), NCHN)
    blocks = 0
    i0 = 0
    for blknum, blkfile in enumerate(data_files):
        if blocks >= NBLK:
            break
        if blkfile != "analysis.py" and blkfile != "root":

            print blkfile, blknum
            data = np.fromfile(blkfile, dtype=np.int16)
            i1 = i0 + NSAM
            for ch in range(NCHN):
                raw_channels[ch][i0:i1] = (data[ch::32])
                # print x
            i0 = i1
            blocks += 1
	


    print "length of data = ", len(raw_channels)
    print "length of data[0] = ", len(raw_channels[0])
    print "length of data[1] = ", len(raw_channels[1])

    for enum, channel in enumerate(raw_channels):
        data_file = open("{}/data_{:02d}.dat".format("root", enum), "wb+")
        channel.tofile(data_file, '')

    return raw_channels
    

def plot_data(total_data):
    client = pykst.Client("NumpyVector")
#    time.sleep(10)
    xdata = np.arange(0, len(total_data[0])).astype(np.float64)
    ccount = 0
    for channel in total_data:
        V1 = client.new_editable_vector(xdata, name="X")
        V2 = client.new_editable_vector(channel.astype(np.float64), name="Y")
        c1 = client.new_curve(V1, V2)
        p1 = client.new_plot()
        p1.add(c1)
        ccount += 1
        if ccount >= 2:
            break



def run_main():
    plot_data(read_data())


if __name__ == '__main__':
    run_main()

