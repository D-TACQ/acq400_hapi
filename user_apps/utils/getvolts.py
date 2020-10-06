'''
Created on 6 Oct 2020

@author: pgm
'''


import urllib.request
import argparse
from lxml import etree
import lxml
import xml.etree.ElementTree as ElementTree

def getvolts(args): 
    while True:
        try:   
            content = urllib.request.urlopen("http://{}/d-tacq/data/volts.xml".format(args.uut[0])).read()
            root = etree.fromstring(content)
            break
        except lxml.etree.XMLSyntaxError:
            continue
        
    for acqdata in root.xpath('//acqData'):
        key = acqdata.attrib['n']
        if key == 'VAN' or key == 'VAP':
             for v in acqdata:
                   print(acqdata.attrib['n'],v.text)


def run_main():
    parser = argparse.ArgumentParser(description='getvolts')
    parser.add_argument('uut', nargs=1)
    getvolts(parser.parse_args())
if __name__ == '__main__':
    run_main()


