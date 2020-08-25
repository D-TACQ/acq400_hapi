# Using acq400_hapi to configure and perform a transient capture

Below are the recommended steps to configure and perform a transient capture on an acq400 series device. The steps are as follows:

 1. Use sync_role to set up clocks.
 2. Use configure_transient to set up transient lengths and triggers.
 3. Use acq400_upload to take the shot, upload and plot the data.

Note that the UUT names used in the example below will not be the same as the UUT names used by the user.

## TL;DR
The full document is recommended reading for new users, but for returning users here are the commands you need to configure your system:

### Internal clock and trigger:

    ./user_apps/acq400/sync_role.py acq2106_279
    ./user_apps/acq400/acq400_configure_transient.py --pre=0 --post=100000 --trg=int,rising acq2106_279
    ./user_apps/acq400/acq400_upload.py --plot=1 --capture=1 --save_data="acq2106_279_{}" acq2106_279

### External clock and trigger

    ./user_apps/acq400/sync_role.py --toprole=fpmaster --fin=1M --fclk=1M acq2106_279
    ./user_apps/acq400/acq400_configure_transient.py --pre=0 --post=100000 --trg=ext,rising acq2106_279
    ./user_apps/acq400/acq400_upload.py --soft_trigger=0 --plot=1 --capture=1 --save_data="acq2106_279_{}" acq2106_279

## Using sync_role

The recommended method to configure clocks on an acq400 series is to use a script called "**sync_role**". This script is available from the command line on the UUT, however it is also available using a python wrapper located here:

    user_apps/acq400/sync_role.py

Note that usually sync_role is run at UUT boot time. It is usually run with some sensible default values. However it is recommended to explicitly run sync_role again at least once in order to make sure that it is run with the exact parameters that the user wants.

### Available command line arguments

To view which arguments are available the script can be run as shown below:

    ./user_apps/acq400/sync_role.py -h
    usage: sync_role.py [-h] [--clk CLK] [--trg TRG] [--sim SIM] [--trace TRACE]
                    [--enable_trigger ENABLE_TRIGGER] [--toprole TOPROLE]
                    [--fclk FCLK] [--fin FIN] [--clkdiv CLKDIV]
                    [--trgsense TRGSENSE]
                    uuts [uuts ...]

    set sync roles for a stack of modules
    
    positional arguments:
      uuts                  uut
    
    optional arguments:
      -h, --help            show this help message and exit
      --clk CLK             int|ext|zclk|xclk,fpclk,SR,[FIN]
      --trg TRG             int|ext,rising|falling
      --sim SIM             s1[,s2,s3..] list of sites to run in simulate mode
      --trace TRACE         1 : enable command tracing
      --enable_trigger ENABLE_TRIGGER
                            set this to enable the trigger all other args ignored
      --toprole TOPROLE     role of top in stack
      --fclk FCLK           sample clock rate
      --fin FIN             external clock rate
      --clkdiv CLKDIV       optional clockdiv
      --trgsense TRGSENSE   trigger sense rising unless falling specified

Not all of the arguments are necessary for basic usage. 

### Use internal clock

To run a simple sync_role the user can do the following:

    user_apps/acq400/sync_role.py acq2106_123

This command will configure the UUT to use the systems own **internal** clock and trigger, which is useful for first time users as there does not need to be any clock or trigger lemos connected. 

### Use external clock

If the user wants to configure for an **external** clock and trigger (trigger settings can be more fully customised later using other scripts) then the following arguments should be used:

    user_apps/acq400/sync_role.py --toprole=fpmaster --fclk=1000000 acq2106_123

Where the **--fclk** argument should be changed to the frequency of the clock being provided.

## Set more specific transient parameters using configure_transient.py

To set parameters like PRE and POST trigger samples or trigger configuration use 

    user_apps/acq400/acq400_configure_transient.py

### Available command line arguments

To view which arguments are available the script can be run as shown below:

    ./user_apps/acq400/acq400_configure_transient.py -h
    usage: acq400_configure_transient.py [-h] [--pre PRE] [--post POST]
                                         [--demux DEMUX] [--clk CLK] [--trg TRG]
                                         [--sim SIM] [--trace TRACE]
                                         uuts [uuts ...]
    
    configure multiple acq400
    
    positional arguments:
      uuts           uut pairs: m1,m2 [s1,s2 ...]
    
    optional arguments:
      -h, --help     show this help message and exit
      --pre PRE      pre-trigger samples
      --post POST    post-trigger samples
      --demux DEMUX  embedded demux
      --clk CLK      int|ext|zclk|xclk,fpclk,SR,[FIN]
      --trg TRG      int|ext,rising|falling
      --sim SIM      s1[,s2,s3..] list of sites to run in simulate mode
      --trace TRACE  1 : enable command tracing

Not all of the options are of immediate use to the user.

### Configuring a POST trigger transient capture using an internal trigger.

To **configure** a transient capture that will take 1e5 samples after an internal trigger is provided the following command line should be used:

    ./user_apps/acq400/acq400_configure_transient.py --pre=0 --post=100000 --trg=int,rising acq2106_123

This will only configure the system and will **not** actually **arm** the system.

### Configuring a POST trigger transient capture using an external trigger.

To configure the system for a **POST** trigger capture, with the trigger set to a front panel TTL trigger the following command line should be used:

    ./user_apps/acq400/acq400_configure_transient.py --pre=0 --post=100000 --trg=ext,rising acq2106_123

To change the number of samples capture the user should change the **--post** argument to their desired transient length.

## Use acq400_upload.py to arm the UUT, upload, and plot data

To arm the system the user should use the following script:

    user_apps/acq400/acq400_upload.py

### Available command line arguments


    ./user_apps/acq400/acq400_upload.py -h
    usage: acq400_upload.py [-h] [--save_data SAVE_DATA] [--plot_data PLOT_DATA]
                            [--trace_upload TRACE_UPLOAD] [--channels CHANNELS]
                            [--soft_trigger SOFT_TRIGGER] [--capture CAPTURE]
                            [--remote_trigger REMOTE_TRIGGER] [--wrtd_tx WRTD_TX]
                            uuts [uuts ...]
    
    acq400 upload
    
    positional arguments:
      uuts                  uut[s]
    
    optional arguments:
      -h, --help            show this help message and exit
      --save_data SAVE_DATA
                            store data to specified directory, suffix {} for shot
                            #
      --plot_data PLOT_DATA
                            1: plot data
      --trace_upload TRACE_UPLOAD
                            1: verbose upload
      --channels CHANNELS   comma separated channel list
      --soft_trigger SOFT_TRIGGER
                            help use soft trigger on capture
      --capture CAPTURE     1: capture data, 0: wait for someone else to capture,
                            -1: just upload
      --remote_trigger REMOTE_TRIGGER
                            your function to fire trigger
      --wrtd_tx WRTD_TX     release a wrtd_tx when all boards read .. works when
                            free-running trigger


Not all of the arguments are necessary for basic usage.

### Arm, upload and plot

    ./user_apps/acq400/acq400_upload.py --plot_data=1 --capture=1 --save_data="acq2106_279_{}" acq2106_279

This command line example will **arm** the UUT (at which point the UUT will either wait for an external trigger or trigger itself using an internal trigger), **wait** for the transient capture to finish and **offload** the data to a directory named acq2106_279_XX where XX is the shot number. The script will then **plot** the data using matplotlib for the user.

### Arm, upload and plot a subset of channels

To tell acq400_upload.py that you're only interested in saving and plotting a subset of the available channels, the user should use the **--channels argument** as shown in the excerpt below:

    user_apps/acq400/acq400_upload.py --plot=1 --channels=1,2,3,4 --capture=1 --save_data="acq2106_279_{}" acq2106_279


