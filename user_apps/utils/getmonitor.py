#!/usr/bin/env python
'''
Created on 6 Oct 2020

@author: pgm

Pulls one of the ACQ400 http ajax monitor files, parses and prints user selected values

Examples:
    [pgm@hoy5 utils]$ ./getmonitor.py --verbose=2 --key='VA[PN]' acq2106_119 acq2106_276
    acq2106_119 VAN -13.1
    acq2106_119 VAP 12.78
    acq2106_276 VAN -13.0
    acq2106_276 VAP 12.89

    ./getmonitor.py --verbose=2 --key='.*AGGSTA.0x0c (\w+).*' --monxml=acq4000.xml \
        acq2106_119 acq2106_261 acq2106_262
    acq2106_119 0x00000066
    acq2106_261 0x00000025
    acq2106_262 0x00000100


'''


import urllib.request
import argparse
from lxml import etree
import lxml
import xml.etree.ElementTree as ElementTree
import re

def getvolts(uut, monxml, kex, verbose=0): 
    while True:
        try:   
            content = urllib.request.urlopen("http://{}/d-tacq/data/{}".format(uut, monxml)).read()
            root = etree.fromstring(content)
            break
        except lxml.etree.XMLSyntaxError:
            continue
        
    for acqdata in root.xpath('//acqData'):
        key = acqdata.attrib['n']
        if kex.match(key):
            value = acqdata[0].text
            if verbose == 2:
                print(uut, key, value)
            elif verbose == 1:
                print(key, value)
            else:
                print(value)
        else:            
            for m in kex.finditer(acqdata[0].text):
                try:
                    value = m.group(1)
                except:
                    value = m.group()
                if verbose == 2:
                    print(uut, value)
                else:
                    print(value)                              


def run_main():
    parser = argparse.ArgumentParser(description='getvolts')
    parser.add_argument('--verbose', default=1, type=int, help='0: print value, 1: print key,value, 2: print uut,key, value')
    parser.add_argument('--monxml', default="volts.xml", help='monitor file to request and parse')
    parser.add_argument('--key', default='VA.', help='key, could be regex')
    parser.add_argument('uuts', nargs='+')
    
    
    args = parser.parse_args()
    kex = re.compile(args.key)
    for uut in args.uuts:
        getvolts(uut, args.monxml, kex, verbose=args.verbose)

if __name__ == '__main__':
    run_main()


