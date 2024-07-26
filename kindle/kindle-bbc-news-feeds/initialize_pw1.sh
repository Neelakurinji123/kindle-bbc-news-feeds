#!/bin/sh

if [ ! -f /tmp/customized_kindle ]; then
	lipc-set-prop com.lab126.pillow disableEnablePillow disable

	trap "" SIGTERM
	stop lab126_gui
	sleep 2
	trap - SIGTERM

	touch /tmp/customized_kindle
fi
