#!/bin/sh

cd "$(dirname "$0")"
IP='192.168.2.2'

if [ -f /tmp/customized_kindle ]; then
	PID=$(ssh root@${IP} "pidof powerd")
	if [ -z $PID ]; then
    	ssh root@${IP} "/etc/init.d/powerd start"
    	ssh root@${IP} "/etc/init.d/framework start"
	fi
	rm /tmp/customized_kindle
	ssh root@${IP} "reboot"
fi

