#!/usr/bin/python
"""
# bigplot.py : example plotting HUGE data

eg
dt100@brotto acq400_hapi]$ ./user_apps/acq400/acq400_upload.py --save_data /data/acq2106_083 --plot_data=1 --capture=-1 --trace_upload=1 --channels=1,2 acq2106_083
acq2106_083 CH01 start..
acq2106_083 CH01 complete.. 0.682 s 35.17 MB/s
acq2106_083 CH02 start..
acq2106_083 CH02 complete.. 0.738 s 32.50 MB/s
KeyboardInterrupt

# matplot lib didn't cut it ..

[dt100@brotto acq400_hapi]$ ls -l /data/acq2106_083/
total 48236
-rw-rw-r--. 1 dt100 dt100 24691356 Jul 14 12:31 acq2106_083_CH01
-rw-rw-r--. 1 dt100 dt100 24691356 Jul 14 12:31 acq2106_083_CH02
-rw-rw-r--. 1 dt100 dt100       50 Jul 14 12:31 format


"""


import pykst
import numpy as np
ch01 = np.fromfile('/data/acq2106_083/acq2106_083_CH01', dtype='int16')
ch02 = np.fromfile('/data/acq2106_083/acq2106_083_CH02', dtype='int16')
llen = len(ch01)
xsam = np.linspace(0, llen, num=llen)
client = pykst.Client("NumpyVector")
X1 = client.new_editable_vector(xsam, name="samples")
Y1 = client.new_editable_vector(ch01.astype(np.float64), name="CH01")
Y2 = client.new_editable_vector(ch02.astype(np.float64), name="CH02")
c1 = client.new_curve(X1,Y1)
p1 = client.new_plot()
p1.add(c1)

p2 = client.new_plot()
c2 = client.new_curve(X1,Y2)
p2.add(c2)

