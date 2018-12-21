
import numpy as np
import matplotlib.pyplot as plt
import time
import subprocess

plt.ion()
dlist = []

for item in range(0, 8):
    dlist.append([])

while True:
    data = subprocess.check_output(["./dumpshm.ai"])
    data = data.replace(" ", "")
    data = data.split(",")
    data = data[:-1]
    print "data = ", data

    for num, list in enumerate(dlist):
        dlist[num].append(data[num])

    for num, list in enumerate(dlist):
        plt.plot(dlist[num])


    plt.draw()
    plt.pause(0.0001)
    plt.clf()
    print "drawing"
    if len(dlist[0]) > 150:
        for num, list in enumerate(dlist):
            dlist[num] = dlist[num][1:-1]
    time.sleep(1)
    num+=1