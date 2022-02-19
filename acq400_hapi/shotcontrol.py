import sys
import threading
import time
import os
import errno

try:
    import matplotlib.pyplot as plt
except Exception as e:
    plt = e

def wait_for_state(uut, state, timeout=0):
    UUTS = [uut]
    time0 = 0
    if time0 == 0:
        time0 = time.time()
    for uut in UUTS:
        olds = ""
        finished = False
        dots = 0
        pollcat = 0

        while not finished:
            st = uut.s0.TRANS_ACT_STATE.split(' ')[1] #Real name TRANS_ACT:STATE
            finished = st == state
            news = "polling {}:{} {} waiting for {}".format(uut.uut, st, 'DONE' if finished else '', state)
            if news != olds:
                sys.stdout.write("\n{:06.2f}: {}".format(time.time() - time0, news))
                olds = news
            else:
                sys.stdout.write('.')
                dots += 1
                if dots >= 20:
                    dots = 0
                    olds = ""
            if not finished:
                if timeout and (time.time() - time0) > timeout:
                    sys.exit("\ntimeout waiting for {}".format(news))
                time.sleep(1)
            pollcat += 1
    print("")


class ActionScript:
    def __init__(self, script_and_args):
        self.sas = script_and_args.split()
        print("ActionScript creates {}".format(self.sas))
    def __call__(self):
        print("ActionScript: call()")
        call(self.sas)



class ShotController:
    """ShotController handles shot synchronization for a set of uuts
    """
    def prep_shot(self):
        for u in self.uuts:
            u.statmon.stopped.clear()
            u.statmon.armed.clear()

        self.tp = [ threading.Thread(target=u.statmon.wait_stopped) for u in self.uuts]

        for t in self.tp:
            t.setDaemon(True)
            t.start()

        self.ta = [threading.Thread(target=u.statmon.wait_armed) for u in self.uuts]

        for t in self.ta:
            t.setDaemon(True)
            t.start()

    def wait_armed(self):
        wdt = threading.Thread(target=self.wdt, kwargs={'wait_list': self.ta})
        wdt.start()
        for t in self.ta:
            t.join()
        wdt.join()

    def wait_complete(self):
        # @@TODO start a watcher task. If one or more has completed, kill the rest after a timeout.
        wdt = threading.Thread(target=self.wdt, kwargs={'wait_list': self.tp}) 
        wdt.start()
        for t in self.tp:
            t.join()
        wdt.join()   

    def wdt(self, wait_list):
        loops_with_zombies = 0
        
        while True:
            alive = 0
            dead = 0
            for t in wait_list:
                if t.is_alive():
                    alive += 1
                else:
                    dead += 1
            if alive == 0:
                return
            elif dead == 0:
                continue
            else:
                loops_with_zombies += 1
                if loops_with_zombies/10 > self.zombie_timeout:
                    print("we have zombies")
                    for ix, u in enumerate(self.uuts):
                        if wait_list[ix].is_alive():
                            print("{} zombie requested to leave".format(u.uut))
                            u.statmon.break_requested = True
            time.sleep(0.1)
                             
            
            
    def arm_shot_action(u):
        def _arm_shot_action():
            print("%s set_arm" % (u.uut))
            u.s0.set_arm = 1
        return _arm_shot_action


    def arm_shot(self):
        thx = [ threading.Thread(target=ShotController.arm_shot_action(u)) for u in self.uuts ]
        for t in thx:
            t.start()
        for t in thx:
            t.join()
        self.wait_armed()

    def abort_shot(self):
        for u in self.uuts:
            print("%s set_abort" % (u.uut))
            u.s0.set_abort = 1

    def on_shot_complete(self):
        """runs on completion, expect subclass override."""
        for u in self.uuts:
            print("%s SHOT COMPLETE shot:%s" % (u.uut, u.s1.shot))

    def run_shot(self, soft_trigger=False, acq1014_ext_trigger=0,
                remote_trigger=None):
        """run_shot() control an entire shot from client.

           for more control, use the individual methods above.

           Args:
               soft_trigger=False (bool) : trigger when armed

        """
        if acq1014_ext_trigger:
            # block external triggers with temp switch to soft trigger
            self.uuts[0].s2.acq1014_trg = 1
        self.prep_shot()
        self.arm_shot()
        if soft_trigger:
            if soft_trigger < 0:
                print("hit return for soft_trigger")
                sys.stdin.readline()
            else:
                while soft_trigger > 1:
                    print("sleep {}".format(soft_trigger))
                    time.sleep(1)
                    soft_trigger = soft_trigger - 1

            print("%s soft_trigger" % (self.uuts[0].uut))
            self.uuts[0].s0.soft_trigger = 1
        elif remote_trigger != None:
            remote_trigger()

        if acq1014_ext_trigger > 0:
            time.sleep(acq1014_ext_trigger)
            self.uuts[0].s2.acq1014_trg = 0

        self.wait_complete()
        self.on_shot_complete()

    def map_channels(self, channels):
        cmap = {}
        #print("map_channels {}".format(channels))
        ii = 0
        for iu, u in enumerate(self.uuts):
            if channels == ():
                cmap[iu] = list(range(1, u.nchan()+1))  # default : ALL
            elif type(channels) == int:
                cmap[iu] = channels                  # single value
            elif type(channels[0]) != tuple:
                cmap[iu] = channels                  # same tuple all UUTS
            else:
                try:
                    cmap[iu] = channels[ii]          # dedicated tuple
                except:
                    cmap[iu] = 1                     # fallback, ch1

            ii = ii + 1
        return cmap

    def read_channels(self, channels=()):
        self.cmap = self.map_channels(channels)
        chx = [u.read_channels(self.cmap[iu]) for iu, u in enumerate(self.uuts)]

        if self.uuts[0].save_data:
            with open("%s/format" % (self.uuts[0].save_data), 'w') as fid:
                for iu, u in enumerate(self.uuts):
                    for ch in self.cmap[iu]:
                        fid.write("%s_CH%02d RAW %s 1\n" % (u.uut, ch, 's'))


        return (chx, len(self.uuts), len(chx[0]), len(chx[0][0]))


    def __init__(self, _uuts, shot=None, zombie_timeout=30):
        self.uuts = _uuts
        self.zombie_timeout = zombie_timeout
        if shot != None:
            for u in self.uuts:
                u.s1.shot = shot


class ShotControllerWithDataHandler(ShotController):
       
    def handle_data(self, args):
        if args.save_data:
            shotdir = args.save_data.format(self.increment_shot(args))
            for u in self.uuts:
                u.save_data = shotdir

        if args.trace_upload:
            for u in self.uuts:
                u.trace = 1

        chx, ncol, nchan, nsam = self.read_channels(eval(args.channels))

    # plot ex: 2 x 8 ncol=2 nchan=8
    # U1 U2      FIG
    # 11 21      1  2
    # 12 22      3  4
    # 13 23
    # ...
    # 18 28     15 16
        if args.plot_data:
            if isinstance(plt, Exception):
                print("Sorry, plotting not available")
            else:                
                                
                for col in range(ncol):
                    for chn in range(0,nchan):
                        fignum = 1 + col + chn*ncol
                        if hasattr(args, 'one_plot'):
                            if not args.one_plot:
                                plt.subplot(nchan, ncol, fignum)
                        else:
                            plt.subplot(nchan, ncol, fignum)
                        plt.suptitle('{} shot {}'.format(args.uuts[0] if len(args.uuts) == 1 else args.uuts, self.uuts[0].s1.shot))
                        if args.plot_data == 2:
                            tb = self.uuts[0].read_transient_timebase(args.post+args.pre, args.pre)
                            plt.xlabel("time [S]")
                            plt.ylabel("Volts")                        
                            line, = plt.plot(tb, self.uuts[col].chan2volts(self.cmap[col][chn], chx[col][chn]))
                            print("legend {}.{:03d}".format(args.uuts[col], self.cmap[col][chn]+1))
                            line.set_label("{}.{:03d}".format(args.uuts[col], self.cmap[col][chn]+1))
                            plt.legend()
                        else:
                            plt.xlabel("sample")
                            plt.ylabel("counts")                           
                            plt.plot(chx[col][chn])
                plt.show()


    @staticmethod
    def save_data_init(args, save_data):
        save_root = os.path.dirname(save_data)        # ignore shot formatter
        if save_root != '':
            try:
                os.makedirs(save_root)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
        else:
            save_root = '.'

        args.shotfile = "{}/SHOT".format(save_root)
        if os.path.exists(args.shotfile):
            with open(args.shotfile) as sf:
                for line in sf:
                    args.shot = int(line)
        else:
            args.shot = 0
            with open(args.shotfile, "w") as sf:
                sf.write("{}\n".format(args.shot))

    @staticmethod
    def increment_shot(args):
        with open(args.shotfile) as sf:
            for line in sf:
                args.shot = int(line)
        args.shot += 1

        with open(args.shotfile, "w") as sf:
                sf.write("{}\n".format(args.shot))
        return args.shot

    def run_shot(self, soft_trigger=False, acq1014_ext_trigger=0,
            remote_trigger=None):
            super().run_shot(soft_trigger, acq1014_ext_trigger, remote_trigger)
            if self.args.save_data or self.args.plot_data:
                self.handle_data(self.args)

    def __init__(self, _uuts, args, shot=None):
        ShotController.__init__(self, _uuts, shot)
        self.args = args
        if args.save_data:
            self.save_data_init(args, args.save_data)

SAVEDATA=os.getenv("SAVEDATA", None)
PLOTDATA=int(os.getenv("PLOTDATA", "0"))
TRACE_UPLOAD=int(os.getenv("TRACE_UPLOAD", "0"))
CHANNELS=os.getenv("CHANNELS", "()")

class ShotControllerUI:
        @staticmethod
        def add_args(parser):
            parser.add_argument('--save_data', default=SAVEDATA, type=str, help="store data to specified directory, suffix {} for shot #")
            parser.add_argument('--plot_data', default=PLOTDATA, type=int, help="1: plot data")
            parser.add_argument('--one_plot', default=None, type=int, help="1: plot data")
            parser.add_argument('--trace_upload', default=TRACE_UPLOAD, type=int, help="1: verbose upload")
            parser.add_argument('--channels', default=CHANNELS, type=str, help="comma separated channel list")
