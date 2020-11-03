
# Using acq400_hapi to perform a transient capture with AWG

Below are the recommended steps to upload a custom AWG file to a UUT, configure that UUT, and perform a transient capture on the UUT. The steps are as follows:

 1. Use sync_role to set up clocks.
 2. Use configure_transient to set up transient lengths and triggers (if the UUT has an AI module)
 3. Use acq400_load_awg.py to upload the data that will be played out of the AO module.
 4. Use acq400_upload to take the shot, upload and plot the data. (if the UUT has an AI module)

Note that the UUT names used in the example below will not be the same as the UUT names used by the user.
Also note that if the user is using an AI module to capture the signal from the AO module, then it is necessary to have read and understood the information contained in the [CAPTURE_README.md](https://github.com/D-TACQ/acq400_hapi/blob/master/user_apps/acq400/CAPTURE_README.md).

## TL;DR
The full document is recommended reading for new users, but for returning users here are the commands you need to configure your system:

### Internal clock and trigger:

    python3 ./user_apps/acq400/sync_role.py --toprole=master --fclk=500k acq2106_130
    python3 ./user_apps/acq400/acq400_configure_transient.py --pre=0 --post=100000 --trg=int,rising acq2106_130
    python3 ./user_apps/acq400/acq400_load_awg.py --file=./32interleaved_sine.dat --mode=1 --soft_trigger=0 --playtrg=int,rising acq2106_130
    python3 ./user_apps/acq400/acq400_upload.py --soft_trigger=1 --plot=1 --capture=1 --save_data="acq2106_130_{}" acq2106_130


### External clock and trigger

    python3 ./user_apps/acq400/sync_role.py --toprole=fpmaster --fin=1M --fclk=500k acq2106_130
    python3 ./user_apps/acq400/acq400_configure_transient.py --pre=0 --post=100000 --trg=ext,rising acq2106_130
    python3 ./user_apps/acq400/acq400_load_awg.py --file=./32interleaved_sine.dat --mode=1 --soft_trigger=0 --playtrg=ext,rising acq2106_130
    python3 ./user_apps/acq400/acq400_upload.py --soft_trigger=0 --plot=1 --capture=1 --save_data="acq2106_130_{}" acq2106_130

Note that the above commands are for a system with an AO424 card and so the clocks have been set to 500kHz for the AO **AND** the AI. This may or may not be a sensible choice for the user.

## Making sure the system is ready for AWG
It is possible that the system in use may not always be immediately configured for AWG output. In order to prime the UUT for AWG use make sure that the following items are in place.

#### The AWG package is in place

 The user can check this by doing the following:

    acq2106_130> ls /mnt/packages/*awg*
    /mnt/packages/11-custom_awg-1910251105.tgz

Note that if the package is **NOT** in place then it can be copied there using the following command:

    cp /mnt/packages.opt/*awg* /mnt/packages/

#### The AO site is in the distributor set

To check that the AO site is included in 'sites' as below:

    acq2106_130> get.site 0 distributor
    reg=0x00408001 sites=5 comms=9 pad=0 DATA_MOVER_EN=on

If the AO site is **NOT** in the distributor the user can set it by using the following command:

    play0 5 

where 5 is the AO site we want to include in the distributor.


## Using sync_role

The explanation and in depth coverage of sync_role is included in [CAPTURE_README.md](https://github.com/D-TACQ/acq400_hapi/blob/master/user_apps/acq400/CAPTURE_README.md). For more information please read this document.


## Set more specific transient parameters using configure_transient.py

*This is only necessary if the user is using an AO card looped back to an AI card.*

The explanation and in depth coverage of configure_transient is included in [CAPTURE_README.md](https://github.com/D-TACQ/acq400_hapi/blob/master/user_apps/acq400/CAPTURE_README.md). For more information please read this document.

## Creating a custom AWG file

Creating a custom AWG file will eventually be a necessary step for the user. The file can be created in MATLAB, octave or any other language the user is familiar with, but for the sake of continuity this README will generate the file using python. To see the composition of an AWG file it is useful for the user to create their own.

### Creating the array using python

To create a single sine wave the user can do the following in python:

```python
    import numpy as np
    import matplotlib.pyplot as plt
    x = np.linspace(0, 8*np.pi, int(1e5))
    y = 32767 * np.sin(x) # full scale in 16 bit DAC codes
    plt.plot(y)
    plt.show()
```
The plot is included to demonstrate what we have done so far:

![enter image description here](https://user-images.githubusercontent.com/36033499/91312594-52564c80-e7ac-11ea-97a1-fe7fb2af27db.png)

Now that there is a variable 'y' which contains a numpy array with a full scale sine wave, the user can begin extending the sine wave over 32 channels.

```python
    interleaved_waves = []
    nchan = 32
    for elem in y:
        interleaved_waves.extend(nchan * [elem])
    
    interleaved_waves = np.array(interleaved_waves).astype(np.int16)
    interleaved_waves.tofile("32interleaved_sine.dat")
```

A new list is created called 'interleaved_waves' which will contain 32 sine waves, where 32 is the number of channels on this specific AO module. The code loops over every element in the 'y' list above and adds an 'nchan' number of elements to the 'interleaved_waves' list. Then the list is cast to 16 bit integers and saved to a file.

Note how the channels are aligned in the array, with sample 1 for channels 1 to 32 being followed by sample 2 for channels 1 to 32 and so on. The user can of course create a different array (and is encouraged to), but the order of samples and channels in the file must always be the same.

## Upload an AWG file to the UUT

To upload an AWG file to the UUT it is recommended to use:

    user_apps/acq400/acq400_load_awg.py

### Available command line arguments

To view which arguments are available the script can be run as shown below:

    python3 user_apps/acq400/acq400_load_awg.py -h
    usage: acq400_load_awg.py [-h] [--file FILE] [--mode MODE]
                              [--awg_extend AWG_EXTEND]
                              [--soft_trigger SOFT_TRIGGER] [--playtrg PLAYTRG]
                              uuts
    
    acq400 load awg simplest
    
    positional arguments:
      uuts                  uut
    
    optional arguments:
      -h, --help            show this help message and exit
      --file FILE           file to load
      --mode MODE           mode: 1 oneshot, 2 oneshot_autorearm
      --awg_extend AWG_EXTEND
                            Number of times the AWG is repeated.
      --soft_trigger SOFT_TRIGGER
                            Emit soft trigger
      --playtrg PLAYTRG     int|ext,rising|falling

Not all of the arguments will be immediately relevant to the user, and the most important ones are covered in the following sections.

### AWG Modes

There are several AWG behavior modes:

1. ONESHOT - Port 54201  
Load the AWG to completion, play buffer once (HIL)

2. ONESHOT+AUTOREPEAT - Port 54202  
Plays the AWG once, stops, starts again at the beginning on trigger  
This is what we demonstrated to NEC.  
=> All these captures are limited by memory size.

3. ONESHOT+CONCURRENT - Port 54203  
Start loading the AWG and start playing while it's still loading (SONY case)

Two other possible modes:

4. CONTINUOUS_REPEAT - Port 54205  
Play the same AWG continuously  
=> the waveform output can continue for a very long time, but it repeats over and over.

5. CONTINUOUS_UPDATE - Port 54206  
Like #2, start playing right away, but like #4, allow the AWG to start playing from the beginning of the buffer again, while filling it up all the time.

The two most common modes are 1 and 2. For more information on other modes please contact D-TACQ.

### Running in mode 1: ONESHOT

    python3 user_apps/acq400/acq400_load_awg.py --file=./32interleaved_sine.dat --mode=1 --soft_trigger=0 --playtrg=int,rising acq2106_130

### Running in mode 2: ONESHOT AUTO-REARM

    python3 user_apps/acq400/acq400_load_awg.py --file=./32interleaved_sine.dat --mode=2 --soft_trigger=0 --playtrg=int,rising acq2106_130

## Use acq400_upload.py to arm the UUT, upload, and plot data

*This is only necessary if the user is using an AO card looped back to an AI card.*

To arm the system the user should use the following script:

    user_apps/acq400/acq400_upload.py

### Available command line arguments

The explanation of arguments available in configure_transient is included in [CAPTURE_README.md](https://github.com/D-TACQ/acq400_hapi/blob/master/user_apps/acq400/CAPTURE_README.md). For more information please read this document.

### Arm, upload and plot

    ./user_apps/acq400/acq400_upload.py --plot_data=1 --capture=1 --save_data="acq2106_279_{}" acq2106_279

This command line example will **arm** the UUT (at which point the UUT will either wait for an external trigger or trigger itself using an internal trigger), **wait** for the transient capture to finish and **offload** the data to a directory named acq2106_279_XX where XX is the shot number. The script will then **plot** the data using matplotlib for the user.

### Arm, upload and plot a subset of channels

To tell acq400_upload.py that you're only interested in saving and plotting a subset of the available channels, the user should use the --**channels argument** as shown in the excerpt below:

    user_apps/acq400/acq400_upload.py --plot=1 --channels=1,2,3,4 --capture=1 --save_data="acq2106_279_{}" acq2106_279

### Viewing a subset of AO channels looped back to AI channels

For the sake of not plotting 32 identical channels, the command line in the section above was used to pull only the first 4 channels of the first AI module (with the AO module connected via VHDCI). The following image was the result:

![enter image description here](https://user-images.githubusercontent.com/36033499/91315252-618ac980-e7af-11ea-8dcb-edd7a43f9583.png)

As can be seen from the image above, the AO module is outputting the wave plotted in the section on creating a sine wave on every channel. 



# Example: site 5 AO424-16 loopback to site 1 AI16

```
python 3 ./user_apps/utils/make_awg_data.py --nchan=16 --len=100000 --offset_by_channel=0.1 sin16op1.dat

python3 ./user_apps/acq400/sync_role.py --toprole=master --fclk=2M acq2106_193
python3 ./user_apps/acq400/acq400_load_awg.py --file=./sin16op1.dat --mode=1 --soft_trigger=0 \
    --playtrg=int,rising --playdiv=2 acq2106_193
python3 ./user_apps/acq400/acq400_upload.py --pre=0 --post=100000 \
	--soft_trigger=1 --trg=int,rising \
	--plot=1 --capture=1 --save_data="acq2106_193_{}" acq2106_193


