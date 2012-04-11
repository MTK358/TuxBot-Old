#!/bin/bash

wrapperlogfile="tuxbotwrapper.log"
ipipe="ipipe"
opipe="opipe"
min_uptime=90
max_consecutive_crashes=5
datefmt="%Y-%m-%dT%H:%M:%S"

if [[ ! -e $ipipe ]]; then
    mkfifo "$ipipe"
elif [[ ! -p $ipipe ]]; then
    echo "\"$ipipe\" already exists and is not a pipe" >&2
fi

if [[ ! -e $opipe ]]; then
    mkfifo "$opipe"
elif [[ ! -p $opipe ]]; then
    echo "\"$opipe\" already exists and is not a pipe" >&2
fi

echo "*** wrapper script started at $(date +"$datefmt")" >> "$wrapperlogfile"

consecutive_crashes=0
while true; do
    echo "*** starting TuxBot at $(date +"$datefmt")" >> "$wrapperlogfile"

    starttime=$(date +%s)
    # TODO this
    python2 TuxBot.py default-config.yaml < "$ipipe" > "$opipe" 2> "$wrapperlogfile"
    endtime=$(date +%s)

    if ((endtime - starttime < min_uptime)); then
        echo "upt"
        ((consecutive_crashes++))
        if ((consecutive_crashes == max_consecutive_crashes)); then
            echo "*** TuxBot crashed in less than $min_uptime seconds $consecutive_crashes time in a row, exiting at $(date +"$datefmt")" >> "$wrapperlogfile"
            break;
        fi
    else
        consecutive_crashes=0
    fi

    echo "*** TuxBot exited at $(date +"$datefmt")" >> "$wrapperlogfile"

    sleep 5
done

echo "*** wrapper script exiting at $(date +"$datefmt")" >> "$wrapperlogfile"

