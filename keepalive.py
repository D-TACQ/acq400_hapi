import acq400_hapi
import time

def test_keepalive(uut_name):
    uut=acq400_hapi.factory(uut_name)
    uut.s0.trace = 1
    uut.keepalive()

    print("sleep 20 then reboot")
    time.sleep(20)
    print("going down 54321")
    uut.s0.reboot = "3210"
    time.sleep(100)


