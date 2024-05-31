#!/bin/sh

cd "$(dirname "$0")"
IP='192.168.2.2'
FILE='bbc_world_screen_flatten.png'
scp images/${FILE} root@${IP}:/tmp
ssh root@${IP} "cd /tmp; /usr/sbin/eips -c"
ssh root@${IP} "cd /tmp; /usr/sbin/eips -g $FILE"
exit 0
