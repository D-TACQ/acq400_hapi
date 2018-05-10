
import numpy as np
import matplotlib.pyplot as plt

current_file = "nofile"

def store_file(it, rdata, nchan, nsam):
    global current_file
    fn = 'DATA/ai%04d.dat' % (it)
    print("store_file {}".format(fn))
    current_file = fn
    with open(fn, 'wb') as f:
        f.write(rdata)

def plot(uut, args, it, rdata):
    nsam = args.post
    nchan = args.nchan
    chx = np.reshape(uut.scale_raw(rdata, volts=args.plot_volts), (nsam, nchan))
    plt.ylabel('Volts' if args.plot_volts else 'Bits')
    plt.xlabel('Samples')
    for ch in range(0, nchan):
        if args.plot_volts:
            plt.plot(uut.chan2volts(ch+1, chx[:,ch]))
        else:
            plt.plot(chx[:,ch])

    plt.show()
    plt.pause(0.0001)



