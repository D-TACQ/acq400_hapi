import epics

verbose = False

class PV_logger(epics.PV):
    def __init__(self, pv):
        epics.PV.__init__(self, pv)
        self.pvname = pv

    def put(self, value, wait=True):
        if verbose:
            print("{}.put({})".format(self.pvname, value))
        super().put(value, wait)

    def get(self):
        value = super().get()
        if verbose:
            print("{}.get() => {}".format(self.pvname, value))
        return value

def pv_factory(uut):
    def _pv_factory(pv):
        return PV_logger("{}:{}".format(uut, pv))
    return _pv_factory