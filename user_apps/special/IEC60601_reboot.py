import acq400_hapi
import socket
import time
import urllib.request
import sys

if len(sys.argv) > 1:
    uut_name = sys.argv[1]
else:
    print("USAGE EC60601_reboot.py host")
    sys.exit(1)

while True:
    uut = None
    print("From the top")

    while not uut:
        contents = None
        while not contents:
            try:
                contents = urllib.request.urlopen("http://{}/d-tacq/rc-local-complete".format(uut_name)).read()
                print(contents)
            except:
                print("uut {} not ready yet".format(uut_name))
                time.sleep(2)
 
        try:
            print('Initializing the UUT...')
            uut = acq400_hapi.factory("{}".format(uut_name))
        except ConnectionRefusedError:
            print('uut hapi interface not ready yet')
            time.sleep(2)
    
    for retry in range(0,3):    
        print('Getting .MODEL .. {}'.format(uut.svc["s{}".format(retry)].MODEL))

    for retry in range(0,3):    
        print('Getting AWG_ACTIVE... {}'.format(uut.s2.AWG_ACTIVE))
        time.sleep(1)

    uut.s0.reboot = "3210"
    time.sleep(3)

    # Housekeeping for next round
    print('Shutting down sockets...')
    uut.close()

    print('Ended')


    time.sleep(3)


