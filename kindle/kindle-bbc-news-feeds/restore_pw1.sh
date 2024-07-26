#!/bin/sh

if [ -f /tmp/customized_kindle ]; then
	cd / && env -u LD_LIBRARY_PATH start lab126_gui
	sleep 2
	lipc-set-prop com.lab126.pillow disableEnablePillow enable
	rm /tmp/customized_kindle
fi