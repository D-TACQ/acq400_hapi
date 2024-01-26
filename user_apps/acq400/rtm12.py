#!/usr/bin/env python
import acq400_hapi
import argparse
import time
from matplotlib import pyplot as plt

''' run an rtm12 shot, providing 3 triggers
    The rtm12 feature allows a shot to be run as 2 bursts of different length
    This setup requires 3 triggers:
        trigger start of capture
        trigger first burst
        trigger second burst
    Then, because a TRANSIENT capture will almost always required a data flush,
        further burst triggers until the capture stops

    We show an example with either soft triggers or WR triggers (txi)

example:

    # Trivial example soft,soft,soft
    /rtm12.py --trg=soft,soft,soft --rtm12=25000,125000 acq1001_084

    #WR example: soft,txi,txi
    /rtm12.py --trg=soft,txi,txi --rtm12=25000,125000 acq1001_084

    soft operates on TRG.d1, txi triggers WRTT1, so it operates on TRG.d1 also

    # transcript: shows the 3 triggers being fired at earliest opportunity.

    ./user_apps/acq400/rtm12.py --trg=soft,txi,txi --rtm12=20000,500000 --siggen=SG0153 --plot=1 acq2106_274

pgm@hoy6:~/PROJECTS/acq400_hapi$ SITECLIENT_TRACE=0 ./user_apps/acq400/rtm12.py --trg=soft,soft,soft --rtm12=25000,125000 acq1001_084
uut ['acq1001_084']
rtm12 [25000, 125000]
trg ['soft', 'soft', 'soft']
0 soft
1 soft
2 soft
trigger capture
trigger burst1
trigger burst2
trigger again to force flush
wait stopped

pgm@hoy6:~/PROJECTS/acq400_hapi$ SITECLIENT_TRACE=1 ./user_apps/acq400/rtm12.py --trg=soft,soft,soft --rtm12=25000,125000 acq1001_084
uut ['acq1001_084']
rtm12 [25000, 125000]
trg ['soft', 'soft', 'soft']
Siteclient(acq1001_084, 4220) >MODEL
Siteclient(acq1001_084, 4220) <acq1002
Siteclient(acq1001_084, 4220) >SITELIST
Siteclient(acq1001_084, 4220) <12,1=427,2=ao
Siteclient(acq1001_084, 4222) >module_name
Siteclient(acq1001_084, 4221) >module_name
Siteclient(acq1001_084, 4222) <ao420fmc
Siteclient(acq1001_084, 4221) <acq427elf
Siteclient(acq1001_084, 4220) >state
Siteclient(acq1001_084, 4220) <0 0 250000 270336 0
Siteclient(acq1001_084, 4220) >transient=PRE=0 POST=250000 SOFT_TRIGGER=0
Siteclient(acq1001_084, 4220) <
Siteclient(acq1001_084, 4220) >rtm12=25000 125000
Siteclient(acq1001_084, 4220) <
0 soft
Siteclient(acq1001_084, 4221) >trg=1,1,1
Siteclient(acq1001_084, 4221) <
1 soft
Siteclient(acq1001_084, 4221) >rgm=3,1,1
Siteclient(acq1001_084, 4221) <
2 soft
Siteclient(acq1001_084, 4221) >sample_count
Siteclient(acq1001_084, 4221) <275000
Siteclient(acq1001_084, 4220) >set_arm=1
Siteclient(acq1001_084, 4220) <
trigger capture
Siteclient(acq1001_084, 4220) >SIG:SRC:TRG:1
Siteclient(acq1001_084, 4220) <SIG:SRC:TRG:1 STRIG
Siteclient(acq1001_084, 4220) >soft_trigger=1
Siteclient(acq1001_084, 4220) <
trigger burst1
Siteclient(acq1001_084, 4220) >SIG:SRC:TRG:1
Siteclient(acq1001_084, 4220) <SIG:SRC:TRG:1 STRIG
Siteclient(acq1001_084, 4220) >soft_trigger=1
Siteclient(acq1001_084, 4220) <
Siteclient(acq1001_084, 4221) >sample_count
Siteclient(acq1001_084, 4221) <275000
Siteclient(acq1001_084, 4221) >sample_count
Siteclient(acq1001_084, 4221) <275000
Siteclient(acq1001_084, 4221) >sample_count
Siteclient(acq1001_084, 4221) <275000
trigger burst2
Siteclient(acq1001_084, 4220) >SIG:SRC:TRG:1
Siteclient(acq1001_084, 4220) <SIG:SRC:TRG:1 STRIG
Siteclient(acq1001_084, 4220) >soft_trigger=1
Siteclient(acq1001_084, 4220) <
Siteclient(acq1001_084, 4221) >sample_count
Siteclient(acq1001_084, 4221) <25000
trigger again to force flush
Siteclient(acq1001_084, 4220) >SIG:SRC:TRG:1
Siteclient(acq1001_084, 4220) <SIG:SRC:TRG:1 STRIG
Siteclient(acq1001_084, 4220) >soft_trigger=1
Siteclient(acq1001_084, 4220) <
Siteclient(acq1001_084, 4221) >sample_count
Siteclient(acq1001_084, 4221) <25000
wait stopped

'''
class BurstHelper(dict):
    __getattr__ = dict.__getitem__
    
    def __init__(self, uut, bursts, triggers):
        self.bufferlen = int(uut.s0.bufferlen)
        self.ssb = int(uut.s0.ssb)
        self.triggers = iter(triggers)

        if bursts[0] < self.bufferlen:
            bursts[0] = self.bufferlen
        bursts[1] += 4 * self.bufferlen

        self.total_samples = sum(bursts)
        self.update(zip(['burst1', 'burst2'], bursts))

        for ii, value in enumerate(triggers):
            print(f'{ii} {value}')
            if ii == 0: uut.s1.trg = f'1,1,1'
            if ii == 1: uut.s1.rgm = f'3,1,1'

    def next_trg(self):
        return next(self.triggers)
    
class TriggerHelper():
    def __init__(self, uut, trg_sync_out):
        self.uut = uut
        self.out = trg_sync_out
        self.total = 0
        self.total_wr = 0
        uut.s0.SIG_TRG_MB_RESET = 1
        try: uut.cC.WR_WRTT1_RESET = 1
        except: pass
    
    def select_sig_src_trg_1(self, source):
        first_time = True
        while acq400_hapi.pv(self.uut.s0.SIG_SRC_TRG_1) != source:
            if first_time:
                self.uut.s0.SIG_SRC_TRG_1 = source
                first_time = False
            time.sleep(0.1)

    def trigger(self, trg_def, delay=2):
        time.sleep(delay)
        print(f'Sending trigger {trg_def}')
        self.total += 1
        if trg_def == 'soft':
            self.select_sig_src_trg_1('STRIG')
            self.uut.s0.soft_trigger = '1'
        elif trg_def == 'txi':
            self.total_wr += 1
            self.select_sig_src_trg_1('WRTT1')
            # --tx_mask=2 selects WRTT1
            self.uut.s0.wrtd_txi = '--tx_mask=2 1'
        else:
            # eg set wrtd_txa
            print(f'TODO: hard_trigger {trg_def}')

    def enable_trig_out(self):
        if self.out:
            self.uut.s0.SIG_SYNC_OUT_TRG = 2 # TRG
            self.uut.s0.SIG_SYNC_OUT_TRG_DX = 1 # d1

    def disable_trig_out(self):
        if self.out:
            self.uut.s0.SIG_SYNC_OUT_TRG = 0 # DO


def state_eq(uut, state):
    if uut.statmon.get_state() == state:
        return True
    return False

def state_not(uut, state):
    if uut.statmon.get_state() != state:
        return True
    return False



def run_main(args):
    assert len(args.trg) == 3, "--trg must have 3 args"
    assert len(args.rtm12) == 2, "--rtm12 must have 2 args"

    print(f'uut {args.uut}')
    print(f'rtm12 {args.rtm12}')
    print(f'trg {args.trg}')

    uut = acq400_hapi.factory(args.uut[0])
    bursts = BurstHelper(uut, args.rtm12, args.trg)
    trg = TriggerHelper(uut, args.trg_sync_out)

    trg.disable_trig_out()

    if state_not(uut, acq400_hapi.STATE.IDLE):
        uut.s0.set_abort
        time.sleep(1)
    
    uut.s0.transient = f'PRE=0 POST={bursts.total_samples} SOFT_TRIGGER=0'
    uut.s0.rtm12 = f'{bursts.burst1} {bursts.burst2}'
    sample_count0 = int(uut.s1.sample_count)
    uut.s0.set_arm = 1
    uut.statmon.wait_armed()


    print("[trigger capture]")
    trg.trigger(bursts.next_trg()) # no need to wait, system is ready for Burst Trigger
        

    print("[trigger burst1]")
    trg.enable_trig_out()
    trg.trigger(bursts.next_trg())

    while int(uut.s1.sample_count) == sample_count0:
        print("waiting for capture to start")
        time.sleep(0.1)

    while int(uut.s1.sample_count) < bursts.burst1:
        print("waiting for burst1")
        time.sleep(0.1)
    time.sleep(1)



    print("[trigger burst2]")
    sample_count0 = int(uut.s1.sample_count)
    sample_count1 = sample_count0
    trg.trigger(bursts.next_trg())
    trg.disable_trig_out()

    while state_eq(uut, acq400_hapi.STATE.RUNPOST):
        sample_count = int(uut.s1.sample_count)
        if sample_count != sample_count0 and sample_count != sample_count1:
            print("trigger again to force flush")
            trg.trigger('soft', 0)
            sample_count1 = sample_count
        else:
            time.sleep(0.1)


    print("[wait stopped]")
    uut.statmon.wait_stopped()

    print(f"script triggers {trg.total} WR {trg.total_wr}")
    print(f"uut triggers {uut.s0.SIG_TRG_MB_COUNT} {uut.cC.WR_WRTT1_COUNT}")

    if args.plot:
        print('plotting')
        for chan, data in enumerate(uut.read_channels(args.plot)):
            plt.plot(data, label=f"CH {args.plot[chan]}")
        plt.legend(loc='upper right')
        plt.show()



def list_of_values(arg):
    return [ int(u) if u.isnumeric() else u for u in arg.split(',') ]
        
def get_parser():
    parser = argparse.ArgumentParser(description='rtm12 demo')
    parser.add_argument('--trg', default="soft,soft,soft", type=list_of_values,
                        help="trg start,b1,b2 soft|wrt=value")
    parser.add_argument('--rtm12', default="33000,99000", type=list_of_values,
                        help="rtm12 b1_len, b2_len")
    parser.add_argument('--trg_sync_out', default=1, type=int,
                        help="Output d1 trg to HDMI")
    parser.add_argument('--plot', default=None, type=list_of_values,
                        help="plot channel results")
    parser.add_argument('uut', nargs=1, help="uut") 
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
