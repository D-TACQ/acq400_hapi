import signal
import sys
import threading
import time

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
        for t in self.ta:
            t.join()
         
    def wait_complete(self):
        for t in self.tp:
            t.join()
            
    def arm_shot(self):
        for u in self.uuts:
            print("%s set_arm" % (u.uut))
            u.s0.set_arm = 1
        self.wait_armed()
            
    def on_shot_complete(self):
        """runs on completion, expect subclass override."""
        for u in self.uuts:
            print("%s SHOT COMPLETE shot:%s" % (u.uut, u.s1.shot))
            
    def run_shot(self, soft_trigger=False):
        """run_shot() control an entire shot from client.
        
           for more control, use the individual methods above.
           
           Args:
               soft_trigger=False (bool) : trigger when armed
               
        """
        self.prep_shot()
        self.arm_shot()
        if soft_trigger:
            print("%s soft_trigger" % (self.uuts[0].uut))
            self.uuts[0].s0.soft_trigger = 1
        self.wait_complete()
        self.on_shot_complete()
        
    def read_channels(self, channels=()):
        uuts = self.uuts        
        chx = [u.read_channels(channels) for u in uuts]
        
        if uuts[0].save_data:
            with open("%s/format" % (uuts[0].save_data), 'w') as fid:            
                for u in uuts:                    
                    for ch in range(1,u.nchan()+1):
                        fid.write("%s_CH%02d RAW %s 1\n" % (u.uut, ch, 's'))
        
        return (chx, len(uuts), len(chx[0]), len(chx[0][0]))
        
    def __init__(self, _uuts):
        self.uuts = _uuts
        for u in self.uuts:
            u.s1.shot = 0                 