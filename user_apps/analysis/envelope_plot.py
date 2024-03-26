#!/bin/python
""" envelope_plot.py: plot frequency transfer function of a filter
    run a transient capture synchronized with a linear sweep.

    capture example:
    ./user_apps/acq400/acq400_fullshot.py --post=100k --channels=1 --trg=ext,rising --capture=1 --save_data acq2106_274/{} acq2106_274

    plot example
    ./user_apps/analysis/envelope_plot.py --coeffs=nyquist acq2106_274/1/acq2106_274_CH01
    ./user_apps/analysis/envelope_plot.py --coeffs=half_nyquist --fmax=2e6 acq2106_274/3/acq2106_274_CH01

"""
import numpy as np
import matplotlib.pyplot as plt
import argparse
import scipy.interpolate


# https://stackoverflow.com/questions/34235530/how-to-get-high-and-low-envelope-of-a-signal
def hl_envelopes_idx(s, dmin=1, dmax=1, split=False):
    """
    Input :
    s: 1d-array, data signal from which to extract high and low envelopes
    dmin, dmax: int, optional, size of chunks, use this if the size of the input signal is too big
    split: bool, optional, if True, split the signal in half along its mean, might help to generate the envelope in some cases
    Output :
    lmin,lmax : high/low envelope idx of input signal s
    """

    # locals min
    lmin = (np.diff(np.sign(np.diff(s))) > 0).nonzero()[0] + 1
    # locals max
    lmax = (np.diff(np.sign(np.diff(s))) < 0).nonzero()[0] + 1

    if split:
        # s_mid is zero if s centered around x-axis or more generally mean of signal
        s_mid = np.mean(s)
        # pre-sorting of locals min based on relative position with respect to s_mid
        lmin = lmin[s[lmin]<s_mid]
        # pre-sorting of local max based on relative position with respect to s_mid
        lmax = lmax[s[lmax]>s_mid]

    # global min of dmin-chunks of locals min
    lmin = lmin[[i+np.argmin(s[lmin[i:i+dmin]]) for i in range(0,len(lmin),dmin)]]
    # global max of dmax-chunks of locals max
    lmax = lmax[[i+np.argmax(s[lmax[i:i+dmax]]) for i in range(0,len(lmax),dmax)]]

    return lmin,lmax

def run_main(args):
    fname = args.data[0]
    raw = np.fromfile(fname, dtype=np.int16)

#    plt.plot(raw)
#    plt.show()

    rootsq = np.sqrt(np.square(raw.astype(float)))
#    plt.plot(rootsq)
#    plt.show()


    rmin, rmax = hl_envelopes_idx(rootsq, dmax=40, dmin=20)
#    plt.plot(freq[rmax], rootsq[rmax])
#    plt.show()

    freq = np.linspace(1, 2000000, 100000)[rmax]
    db = np.multiply(np.log(rootsq[rmax]), 20)
    zerodb = np.mean(db[:100])
    db = np.subtract(db, zerodb)
#    plt.plot(freq[rmax], db)
#    plt.show()

    print(f'length db {len(db)}')
    three_dbs = np.where(db.astype(int) == -3)
    print(three_dbs)
    three_db = three_dbs[0][0]
    print(three_db)



    fig, ax = plt.subplots(1)
    fig.suptitle(f'Frequency response for {fname} coeffs:{args.coeffs}')
    ax.set_ylabel('db')
    ax.set_xlabel('frequency')
    ax.plot(freq, db)
    print(f'3db {freq[three_db]:.3f} {db[three_db]:.0f}')
#                xy=(freq[three_db], db[three_db]), xycoords='data',
    ax.annotate(f'3db point = {freq[three_db]:.3e}', 
                xy=(freq[three_db], db[three_db]), xycoords='data',
                xytext=(0.75, .90), textcoords='axes fraction', 
                va='top', ha='left', arrowprops=dict(facecolor='black', shrink=0.05))
#                (ax.transData.transform((freq[three_db], db[three_db]))))
    plt.show()

def get_parser():
    parser = argparse.ArgumentParser(description='Plot Envelope of frequency sweep')
    parser.add_argument('--fmax', default=2e6, help='frequency at maximum of plot')
    parser.add_argument('--coeffs', default='default', help='name of coefficient set')
    parser.add_argument('data', nargs=1, help='data file to plot')
    return parser

if __name__ == '__main__':
    run_main(get_parser().parse_args())
