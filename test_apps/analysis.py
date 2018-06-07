import pykst
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
import time
import gc


def create_npdata(channum):
    total_data = []
    a = []
    for counter in range(channum):
        total_data.append(a)
    npdata = np.zeros((32, 524288*2*32*4), dtype=np.int16)
    # print "length of data = ", len(total_data)
    # print "npdata = ", npdata
    return npdata


def read_data(total_data):
    #print "dir contents: ", listdir("./")
    current_dir_contents = listdir("./")
    for num, counter in enumerate(current_dir_contents):
        if counter != "analysis.py" and counter != "root":

            print counter, num
            data = np.fromfile(counter, dtype=np.int16)
            for x in range(32):
                # print data[counter::8]
                # total_data[counter].extend(data[counter::8])
                # print len(total_data[x][num * 524288 : (num + 1) * 524288])
                #total_data[x][num * 524288 * 2 : (num + 1) * 524288 * 2] = (data[x::32])
                # print len(data[x::32])
                total_data[x][num * 524288 * 2: (num + 1) * 524288 * 2] = (data[x::32])
                # print x


    print "length of data = ", len(total_data)
    print "length of data[0] = ", len(total_data[0])
    print "length of data[1] = ", len(total_data[1])

    for enum, channel in enumerate(total_data):
        data_file = open("{}/data{}.dat".format("root", enum), "wb+")
        channel.tofile(data_file, '')

    # return total_data

    client = pykst.Client("NumpyVector")
    print "DEBUG - KST"
    #time.sleep(10)
    for channel in total_data:
        xdata = [float(i) for i in channel[0::64]]
        xdata = np.array(xdata)
        gc.collect()
        ydata = [float(i) for i in list(range(0, len(xdata)))]
        gc.collect()
        ydata = np.array(ydata)
        V1 = client.new_editable_vector(xdata, name="X")
        V2 = client.new_editable_vector(ydata, name="Y")
        c1 = client.new_curve(V2, V1)
        p1 = client.new_plot()
        p1.add(c1)
        #return


def plot_data(total_data):
    client = pykst.Client("NumpyVector")
    time.sleep(10)
    for channel in total_data:
        xdata = channel
        ydata = [float(i) for i in list(range(0, len(xdata)))]
        ydata = np.array(ydata)
        V1 = client.new_editable_vector(xdata, name="X")
        V2 = client.new_editable_vector(ydata, name="Y")
        c1 = client.new_curve(V2, V1)
        p1 = client.new_plot()
        p1.add(c1)
        return


def run_main():
    total_data = create_npdata(64)
    read_data(total_data)
    # verify_data()
    # plot_data(total_data)


if __name__ == '__main__':
    run_main()
