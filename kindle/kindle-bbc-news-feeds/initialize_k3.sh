#!/bin/sh

cd "$(dirname "$0")"
IP='192.168.2.2'

if [ ! -f /tmp/customized_kindle ]; then
	PID=$(ssh root@${IP} "pidof powerd")
	if [ -n "$PID" ]; then
    	ssh root@${IP} "/etc/init.d/powerd stop"
    	ssh root@${IP} "/etc/init.d/framework stop"
	fi
	touch /tmp/customized_kindle
fi