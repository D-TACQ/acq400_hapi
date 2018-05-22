
import numpy as np
import matplotlib.pyplot as plt
import argparse


def create_array(size, value):
    # function that creates a numpy array with "size" elements
    # all of which are = value
    waveform = np.zeros((size))
    for index, x in np.ndenumerate(waveform):
        waveform[index] = value
    waveform = waveform.astype(np.int16)
    print(waveform)
    return waveform


def write_array_to_disk(waveform, dir):
    # function that writes numpy array to disk.
    #np.savetxt(dir, waveform)
    waveform.tofile(dir, "")


def generate_awg(args):
    #function that generates an awg waveform
    waveform = create_array(args.size, args.value)
    write_array_to_disk(waveform, args.dir)


def run_main():
    parser = argparse.ArgumentParser(description='generate awg waveform')
    parser.add_argument('--size', default=320000, type=int, help="Size of array to generate.")
    parser.add_argument('--value', default=16384, type=int, help="What vlaues to store in array.")
    parser.add_argument('--dir', default="waves/dc_line", type=str, help="Location to save files")
    generate_awg(parser.parse_args())


if __name__ == '__main__':
    run_main()
