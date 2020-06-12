# create_gpg_stl.py

## Usage

create_gpg_stl.py loads a local JSON file created in the style of a wavedrom JSON file to create an STL file. This STL file can then loaded to acq400 series digital output devices. This makes it easier for users to create their own custom digital output patterns and use them with their digital output device.

An example STL file would be something like this:

    {"signal": [
      {"name": "req", "wave": "0.1..0|1.01|01"},
      {"name": "ack", "wave": "01....|01.1|10"}
    ]}

Note that this example is only two channels for the sake of brevity. Save this to a file inside the test_apps directory and then use the load_wd.py script like so:

    python3 create_gpg_stl.py --file="./wd.json"

This will print the corresponding STL to the terminal, but will also save it to ./wd.stl. It should look something like this if you are using the above example:

    0 0x0
    1 0x2
    2 0x3
    5 0x2
    106 0x1
    107 0x3
    108 0x2
    109 0x3
    210 0x2
    211 0x1

The left hand column is where the signal changes and the right hand column is what the signal changes to.

## Explanation of WaveDrom signals

The WaveDrom signals above are a collection of 1s, 0s, .s, and |s. There are other symbols available for use in WaveDrom but these are not yet supported.

| Symbol  | Meaning  |
| ------------ | ------------ |
| 0  |  Signal low |
|  1 |  Signal high |
|  . |  Same as previous (low or high) |
|  &#124; |  Multiple of previous signal (default 100) |

### Pipes as breaks

The pipe can be configured to by a single, repeatable gap or the user can pass a list of delays to use for the pipe. If we use our example from the previous section and adjust our command to:

    python3 create_gpg_stl.py --file="./wd.json" --breaks="100,300"

In our original example the output STL will now change to the following:

    0 0x0
    1 0x2
    2 0x3
    5 0x2
    106 0x1
    107 0x3
    108 0x2
    109 0x3
    410 0x2
    411 0x1

Notice that instead of increasing by 100 again (to 210), we increase by 300 (to 410) where the second pipe is located.

## Combining single channel STL files

The script can also be used to combine single channel STL files into a single STL file to be loaded to the acq400 series digital output device. Here is a simple example of combining three single channel STL files into a single STL file which could be loaded to the device:

### Single channel STL files:

In this example these STL files are saved to disk so the script can pick them up:

ta.stl:

    0 0
    100 1
    110 0

tb.stl:

    0 0
    200 1
    210 0
    400 1
    410 0

and tc.stl:

    0 0
    100 1
    110 0
    1000 1
    1010 0


### Command to combine the files:

To combine the files we can use the following command:

    python3 create_gpg_stl.py  --stl=d0=ta.stl,d1=tb.stl,d2=tc.stl

This will then output the following:

    0 0x0
    100 0x5
    110 0x0
    200 0x2
    210 0x0
    400 0x2
    410 0x0
    1000 0x4
    1010 0x0

Which is the correct composite STL from the combination of the three waves above. The STL is also saved to disk. The name of the output file can be configured from the command line using the --output_file parameter.

