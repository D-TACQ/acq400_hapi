import numpy as np
import matplotlib.pyplot as plt

import argparse
import acq400_hapi
from user_apps.acq400 import sync_role, acq400_configure_transient, acq400_load_awg, acq400_upload
import os
import re
import shlex


x = np.linspace(0, 8*np.pi, int(1e5))
print(x)
y = 32767 * np.sin(x) # full scale in 16 bit DAC codec

#plt.plot(y)
#plt.show()


# Extend since wave over nchan channels
interleaved_waves = []
nchan = 16
for elem in y:
    interleaved_waves.extend(nchan*[elem])

interleaved_waves = np.array((interleaved_waves)).astype(np.int16)
interleaved_waves.tofile('32interleaved_sine.dat')


class DEFAULTS():
    uutIPAddress = ["acq2106_189"]
    awgFile = "32interleaved_sine.dat"
    SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
    CAPTURE=int(os.getenv("CAPTURE", "1"))
    PLAYTRIGGER = 'int,rising'


def sync_role_config_and_execute():
    print("sync_role_config_and_execute")
    #parser = argparse.ArgumentParser(description="configure single or multiple acq400")
    argString = '--toprole=master --fclk=500k {}'.format(DEFAULTS.uutIPAddress[0])
    args = sync_role.get_args(shlex.split(argString))
    sync_role.run_shot(args)
    #print(parser.parse_args())


def acq400_configure_transient_config_and_execute():
    print("acq400_configure_transient_config_and_execute")
    parser = argparse.ArgumentParser(description="configure single or multiple acq400")
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    argString = '--pre=0 --post=100000 --trg=int,rising {}'.format(DEFAULTS.uutIPAddress[0])
    args = acq400_configure_transient.get_args(shlex.split(argString))
    acq400_configure_transient.configure_shot(args, [acq400_hapi.Acq400(u) for u in args.uuts])


def acq400_load_awg_config_and_execute():
    print("acq400_load_awg_config_and_execute")
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    argString = '--file=./32interleaved_sine.dat --aosite=5 --mode=1 --soft_trigger=0 --playtrg=int,rising {}'.format(DEFAULTS.uutIPAddress[0])
    args = acq400_load_awg.get_args(shlex.split(argString))
    acq400_load_awg.load_awg_top(args)


def acq400_upload_config_and_execute():
    print("acq400_upload_config_and_execute")
    parser = argparse.ArgumentParser(description='acq400 upload')
    acq400_hapi.ShotControllerUI.add_args(parser)
    argString = '--soft_trigger=1 --plot=1 --capture=1 --save_data="acq2106_130" {}'.format(DEFAULTS.uutIPAddress[0])
    args = acq400_upload.get_args(shlex.split(argString))

    # deduplicate (yes, some non-optimal apps call with duplicated uuts, wastes time)
    args.uuts = acq400_upload.uniq(args.uuts)
    # encourage single ints to become a list
    if re.search(r'^\d$', args.channels) is not None:
        args.channels += ','
    args.shot = None
    acq400_upload.upload(args)

def edit_ao_settings():
    uut = acq400_hapi.Acq400(DEFAULTS.uutIPAddress[0])
    uut.s5.clk = "1,2,1"
    uut.s5.clkdiv = "1"
    return None


edit_ao_settings()
sync_role_config_and_execute()
acq400_load_awg_config_and_execute()
acq400_configure_transient_config_and_execute()
acq400_upload_config_and_execute()


