import numpy as np
import matplotlib.pyplot as plt

import argparse
import acq400_hapi
from user_apps.acq400 import sync_role, acq400_configure_transient, acq400_load_awg, acq400_upload
import os
import re

x = np.linspace(0, 8*np.pi, int(1e5))
print(x)
y = 32767 * np.sin(x) # full scale in 16 bit DAC codec

plt.plot(y)
plt.show()


# Extend since wave over nchan channels
interleaved_waves = []
nchan = 16
for elem in y:
    interleaved_waves.extend(nchan*[elem])

interleaved_waves = np.array((interleaved_waves)).astype(np.int16)
interleaved_waves.tofile('32interleaved_sine.dat')


class DEFAULTS():
    uutIPAddress = ["172.25.226.231"]
    awgFile = "32interleaved_sine.dat"
    SOFT_TRIGGER=int(os.getenv("SOFT_TRIGGER", "1"))
    CAPTURE=int(os.getenv("CAPTURE", "1"))
    PLAYTRIGGER = 'int,rising'


def sync_role_config_and_execute():
    parser = argparse.ArgumentParser(description="Testing arg parser for arg addition")
    acq400_hapi.Acq400UI.add_args(parser, post=False)
    parser.add_argument('--enable_trigger', default=None, help="set this to enable the trigger all other args ignored")
    parser.add_argument('--toprole', default='master', help="role of top in stack")
    parser.add_argument('--fclk', default='1000000', help="sample clock rate")
    parser.add_argument('--fin',  default='1000000', help="external clock rate")
    parser.add_argument('--clkdiv', default=None, help="optional clockdiv")
    parser.add_argument('--trgsense', default='rising', help="trigger sense rising unless falling specified")
    parser.add_argument('--uuts', default=DEFAULTS.uutIPAddress, help="uut ")
    sync_role.run_shot(parser.parse_args())
    print(parser.parse_args())


def acq400_configure_transient_config_and_execute():
    parser = argparse.ArgumentParser(description="configure single or multiple acq400")
    acq400_hapi.Acq400UI.add_args(parser, transient=True)
    parser.add_argument('--uuts', default=DEFAULTS.uutIPAddress ,help="uut pairs: m1,m2 [s1,s2 ...]")
    args = parser.parse_args()
    args.trg = "int,rising"
    args.post= 100000
    acq400_configure_transient.configure_shot(args, [acq400_hapi.Acq400(u) for u in args.uuts])


def acq400_load_awg_config_and_execute():
    parser = argparse.ArgumentParser(description='acq400 load awg simplest')
    parser.add_argument('--file', default=DEFAULTS.awgFile, help="file to load")
    parser.add_argument('--mode', default=1, type=int, help="mode: 1 oneshot, d=2 oneshot_autorearm")
    parser.add_argument('--awg_extend', default=1, type=int, help='Number of times the AWG is repeated.')
    parser.add_argument('--soft_trigger', default=0, type=int, help='Emit soft trigger d=1')
    parser.add_argument('--playtrg', default=DEFAULTS.PLAYTRIGGER, help='int|ext,rising|falling')
    parser.add_argument('--uuts', default=DEFAULTS.uutIPAddress, help="uut ")
    print(parser.parse_args())
    acq400_load_awg.load_awg(parser.parse_args())


def acq400_upload_config_and_execute():
    parser = argparse.ArgumentParser(description='acq400 upload')
    acq400_hapi.ShotControllerUI.add_args(parser)
    parser.add_argument('--soft_trigger', default=DEFAULTS.SOFT_TRIGGER, type=int, help="help use soft trigger on capture")
    #parser.add_argument('--plot_data', default=1, type=int, help="plot data")
    parser.add_argument('--capture', default=DEFAULTS.CAPTURE, type=int, help="1: capture data, 0: wait for someone else to capture, -1: just upload")
    parser.add_argument('--remote_trigger', default=None, type=str, help="your function to fire trigger")
    parser.add_argument('--wrtd_tx', default=0, type=int, help="release a wrtd_tx when all boards read .. works when free-running trigger")
    parser.add_argument('--uuts', default=DEFAULTS.uutIPAddress, help="uut[s]")
    args = parser.parse_args()
    # deduplicate (yes, some non-optimal apps call with duplicated uuts, wastes time)
    args.uuts = acq400_upload.uniq(args.uuts)
    # encourage single ints to become a list
    if re.search(r'^\d$', args.channels) is not None:
        args.channels += ','
    args.plot_data = 1
    args.channels = "1"
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
uut = acq400_hapi.Acq400(DEFAULTS.uutIPAddress[0])
uut.s1.trg = "1,1,1"
acq400_configure_transient_config_and_execute()
acq400_upload_config_and_execute()


