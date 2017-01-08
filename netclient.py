#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 12:36:38 2017

@author: pgm
"""


import socket
import re
import sys

def receive_message(sock, termex, maxlen=4096):
    """
    Read the information from the socket, in a buffered
    fashion, receiving only 4096 bytes at a time.

    Parameters:
    sock - The socket object
    termex - re for terminator
    maxlen - max bytes to receive per read
    """
    buffer = ""
    data = ""
    match = None
    while match == None:
        data = sock.recv(maxlen)
        buffer += data
        match = termex.search(buffer)

    # Remove the end message string
    buffer = buffer[:-len(match.group(0))]
    #print("receive_message returns %s" % (buffer))
    return buffer

class Netclient:
    sock = False

    def __init__(self, addr, port) :
        self.__addr = addr
        self.__port = int(port)
        self.sock = socket.socket()
        self.sock.connect((self.__addr, self.__port))

    @property
    def addr(self):
        return self.__addr
    
    @property
    def port(self):
        return self.__port


class Siteclient(Netclient):
    def send(self, message):
        self.sock.send((message+"\n").encode())

    def recv(self):
        return receive_message(self.sock, self.termex)
      
    def sr(self, message):
        self.send(message)
        return self.recv()
 
    def build_knobs(self, knobstr):
        self.knobs = dict((key, 1) for key in knobstr.split())

    def __getattr__(self, name):
        if self.knobs[name] != None:
                return self.sr(name)
        else:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError(msg.format(type(self).__name__, name))

           
    def __init__(self, addr, port):
        Netclient.__init__(self,addr, port)
        self.termex = re.compile(r"(acq400.[0-9] [0-9]+ >)")
        self.send("prompt on")
        self.recv()
        self.send("help")
        self.build_knobs(self.recv())        


if __name__ == '__main__':
    SERVER_ADDRESS = '10.12.132.18'
    SERVER_PORT=4220

    if len(sys.argv) > 1:
        SERVER_ADDRESS = sys.argv[1]
        if len(sys.argv) > 2:
            SERVER_PORT = int(sys.argv[2])

    print("create Netclient %s %d" %(SERVER_ADDRESS, SERVER_PORT))
    svc = Siteclient(SERVER_ADDRESS, SERVER_PORT)
    
    while True:
        try:
            data = raw_input("Enter some data: ")
        except EOFError:
            print("\nOkay. Leaving. Bye")
            break

        print("Hello")

        if not data:
            print("Can't send empty string!")
            print("Ctrl-D [or Ctrl-Z on Windows] to exit")
            continue
        print("< %s" % (data))

        data += "\n"
        svc.send(data)
        data = svc.recv()
        
        print("Got this string from server:")
        print(data + '\n')

        print("Model: %s" % (svc.MODEL))


    
