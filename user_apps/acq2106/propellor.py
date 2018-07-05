class Propellor:
    prop_ix = 0
    props = [ "|", "/", "-", "\\" ]

    @staticmethod
    def spin():
        pstat = Propellor.props[Propellor.prop_ix]
        i2 = Propellor.prop_ix + 1
        if i2 >= len(Propellor.props):
            i2 = 0
        Propellor.prop_ix = i2
        return pstat


