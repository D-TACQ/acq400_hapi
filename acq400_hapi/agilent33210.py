"""
agilent33210 : SCPI insterface to function generator
"""


import socket

class Agilent33210A:
    def __init__(self, ipaddr):
        self.socket = socket.socket()
        self.socket.connect((ipaddr, 5025))
        
    def trigger(self):
        self.socket.send("TRIG\n".encode())


