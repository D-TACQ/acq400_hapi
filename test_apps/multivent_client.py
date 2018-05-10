#!/usr/local/bin/python
# UUT is running continuous pre/post snapshots
# subscribe to the snapshots and save all the data.

import threading
import epics
import argparse
import time
import datetime
import os

NCHAN = 16

# WF record, raw binary (shorts)
WFNAME = ":1:AI:WF:{:02d}"
# alt WF record, VOLTS. Kindof harder to store this in a portable way..
#WFNAME = ":1:AI:WF:{:02d}:V.VALA""

#1:AI:WF:08:V.VALA
class Uut:
    root = "DATA"
    def make_file_name(self, upcount):
        timecode = datetime.datetime.now().strftime("%Y/%m/%d/%H/%M/")
        return self.root+"/"+timecode +"{:06d}".format(upcount)
        
    def store_format(self, path):
        # created a kst / dirfile compatible format file
        fp = open(path+"/format", "w")
        fp.write ("# format file {}\n".format(path))
        # TODO enter start sample from event sample count
        fp.write ("START_SAMPLE CONST UINT32 0\n")
        fp.writelines(["CH{:02d} RAW s 1\n".format(ch) for ch in range(1,NCHAN+1)])
        fp.close()
        
    def on_update(self, **kws):
        self.upcount = self.upcount + 1
        fn = self.make_file_name(self.upcount)
        print(fn)
        if not os.path.isdir(fn):
            os.makedirs(fn)
            
        for ch in range(1, NCHAN+1):            
            yy = self.channels[ch-1].get()            
            yy.astype('int16').tofile(fn+"/CH{:02d}".format(ch))            
            
        self.store_format(fn)
        print("{} {}".format(kws['pvname'], kws['value']))
        
        print(self.channels[1])
        
    def monitor(self):
        self.channels = [epics.PV(self.name+WFNAME.format(ch)) for ch in range(1, NCHAN+1)]
        updates = epics.PV(self.name + ":1:AI:WF:01:UPDATES", auto_monitor=True, callback=self.on_update)
        
    def __init__(self, _name):
        self.name = _name
        self.upcount = 0
        threading.Thread(target=self.monitor).start()
        

def multivent(parser):
    uuts = [Uut(_name) for _name in parser.uuts]
    for u in uuts:
        u.root = parser.root
        
    while True:
        time.sleep(0.5)
    
def run_main():
    parser = argparse.ArgumentParser(description='acq400 multivent')
    parser.add_argument('--root', type=str, default="DATA", help="output root path")
    parser.add_argument('uuts', nargs='+', help="uut names")
    multivent(parser.parse_args())

# execution starts here
if __name__ == '__main__':
    run_main()
