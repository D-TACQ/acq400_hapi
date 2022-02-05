import acq400_hapi
import socket
import time

while True:

    print('Initializing the UUT...')
    uut = acq400_hapi.factory("acq1001_368")
    
    print('Getting AWG_ACTIVE...')
    print(uut.s2.AWG_ACTIVE)

    # Housekeeping for next round
    print('Shutting down sockets...')
    uut.svc['s0'].sock.shutdown(socket.SHUT_RDWR)
    uut.svc['s1'].sock.shutdown(socket.SHUT_RDWR)
    uut.svc['s2'].sock.shutdown(socket.SHUT_RDWR)

    print('Closing sockets...')
    uut.svc['s0'].sock.close()
    uut.svc['s1'].sock.close()
    uut.svc['s2'].sock.close()

    print('Deleting uut from memory...')
    uut.uuts_methods.clear()
    uut.uuts.clear()
    del uut

    print('Ended')


    time.sleep(3)


