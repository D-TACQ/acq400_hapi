#!/bin/sh

#./awg_interweave_loop.sh ao_uut acq_uut 
#./awg_interweave_loop.sh ao_uut acq_uut true #turbo mode
#./awg_interweave_loop.sh ao_uut acq_uut false /some/path/acq400_hapi

set -e

#args
ao_uut=${1:-'acq1001_074'}
acq_uut=${2:-'acq1001_301'}
turbo=${3:-false} #enable turbo on uut first #> bb load --mode 1 --port 52233
hapi_dir=${4:-'.'} #assumes script being run from hapi dir

#file vars
log_file='/tmp/awg_swapper.log'
times_file='/tmp/awg_times.tmp'
data_dir=/tmp/awg_data
data_file=${data_dir}/${acq_uut}_CH01

#waveforms vars
wave1="dat_files/32CH_10V_16384_SHORTED_PRODTESTx32.dat"
wave1_min=510
wave1_max=520
wave2="dat_files/32CH_10V_16384_SHORTED_PRODTESTx64.dat"
wave2_min=970
wave2_max=980

#cmd shorthand
arm_uut="${hapi_dir}/user_apps/acq400/acq400_arm.py"
config_transient="${hapi_dir}/user_apps/acq400/acq400_configure_transient.py --post=100000 --trg=ext,rising"
load_awg="${hapi_dir}/user_apps/acq400/acq400_load_awg.py --auto_soft_trigger=1 --reps=1 --mode=1 --aosite=1"
load_awg_turbo="${hapi_dir}/user_apps/acq400/acq400_load_awg.py --auto_soft_trigger=1 --reps=1 --mode=1 --aosite=1 --port=52233"
wait_state="${hapi_dir}/user_apps/acq400/acq400_wait_state.py"
upload_data="${hapi_dir}/user_apps/acq400/acq400_upload.py --channels=1 --save_data=${data_dir}"

if $turbo; then
    load_awg=$load_awg_turbo
fi

shots=0
file=''
min=0
max=0

$config_transient $acq_uut
echo "started" >> $log_file

while true; do
    shots=$((shots+1))
    echo "\nSHOT $shots"

    if [ "$file" = "$wave1" ]; then
        file=$wave2
        min=$wave2_min
        max=$wave2_max
    else
        file=$wave1
        min=$wave1_min
        max=$wave1_max
    fi

    echo "[CMD] $arm_uut $acq_uut"
    $arm_uut $acq_uut

    echo "[CMD] $wait_state --state=ARM $acq_uut"
    $wait_state --state=ARM $acq_uut

    echo "[CMD] time --output=$times_file -p $load_awg --file=$file $ao_uut"
    /usr/bin/time --output=$times_file -p  $load_awg --file=$file $ao_uut
    runtime=$(cat $times_file | grep real | cut -d" " -f2)

    echo "[CMD] $wait_state --state=IDLE $acq_uut"
    $wait_state --state=IDLE $acq_uut

    rm -fr data/
    echo "[CMD] $upload_data $acq_uut"
    $upload_data $acq_uut

    echo "[CMD] python -c import numpy as np;print(len(np.where(np.diff(np.signbit(np.fromfile('$data_file', dtype=np.int32))))[0]))"
    zc=$(python -c "import numpy as np;print(len(np.where(np.diff(np.signbit(np.fromfile('$data_file', dtype=np.int32))))[0]))")

    if [ "${min}" -lt "$zc" ] && [ "${max}" -gt "$zc" ]; then
        echo $zc is in range
        echo "SHOT ${shots} Passed ${zc} ${runtime}s" >> $log_file
    else
        echo "Error ${zc} is outside range"
        echo "SHOT ${shots} Failed ${zc} ${runtime}s" >> $log_file
    fi
done