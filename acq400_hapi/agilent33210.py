"""
agilent33210 : SCPI insterface to function generator
"""

import os
import time
import socket

class Agilent33210A:
    def __init__(self, ipaddr):
        self.ipaddr = ipaddr
        self.socket = socket.socket()
        self.socket.connect((ipaddr, 5025))
        self.trace = int(os.getenv("A33210A_TRACE", "0"))

    def send(self, str):
        if self.trace:
            print("A33210:{} > {}".format(self.ipaddr, str))
        self.socket.send("{}\n".format(str).encode())

    def trigger(self):
        self.send("TRIG")

    def beep(self, sleep = 0.5):
        self.send("SYST:BEEP")
        time.sleep(sleep)
        self.send("SYST:BEEP")

    def config(self, freq, volts=1, shape="SIN"):
        self.send("VOLT {}".format(volts))
        self.send("OUTP:SYNC ON")
        self.send("FREQ {}".format(freq))
        self.send("FUNC:SHAP {}".format(shape))
        self.send("BURS:STAT OFF")
        self.send("TRIG:SOUR IMM")

    def config_burst(self, ncyc=1):
        self.send("BURS:STAT ON")
        self.send("BURS:NCYC {}".format(ncyc))
        self.send("TRIG:SOUR BUS")

    def config_free_running_burst(self, ncyc=1, rate=1):
        self.send("SYST:BEEP")
        self.send("OUTP OFF")
        self.send("TRIG:SOUR IMM")
        self.send("BURS:INT:PER {}".format(rate))
        self.send("BURS:NCYC {}".format(ncyc))
        self.send("BURS:MODE TRIG")
        self.send("OUTP ON")
