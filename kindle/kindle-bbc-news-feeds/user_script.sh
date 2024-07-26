#!/bin/sh

cd "$(dirname "$0")"
FILE='bbc_world_screen_768x1024.png'
cp images/${FILE} /tmp
cd /tmp
/usr/sbin/eips -c -f
/usr/sbin/eips -g $FILE
exit 0
