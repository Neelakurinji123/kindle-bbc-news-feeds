#!/bin/sh

cd "$(dirname "$0")"
FILE='bbc_world_screen_768x1024.png'
FILE_DARK='bbc_world_screen_dark_768x1024.png'

cond=$(python3 ./daytime.py)

if [ "$cond" == "night" ]; then
    FILE=$FILE_DARK
fi

cp images/${FILE} /tmp
cd /tmp
/usr/sbin/eips -c -f
/usr/sbin/eips -g $FILE
exit 0
