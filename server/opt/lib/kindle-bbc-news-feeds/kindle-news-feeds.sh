#!/bin/sh

IP='192.168.2.2'

# Kindle's daemons must stop.
p=`ssh root@${IP} 'pidof powerd'` 
if [ "$p" != '' ]; then
	ssh root@${IP} "/etc/init.d/powerd stop"
	ssh root@${IP} "/etc/init.d/framework stop"
fi

cd "$(dirname "$0")"
/usr/bin/python3 SVG.py $1
sleep 3
source /tmp/KindleNewsStation.env
s=$(expr $duration \* 60)
echo "test $s"
while [ $repeat -ge 0 ]; do
	repeat=$(expr $repeat - 1)
	for PNGfile in $filelist; do
		scp /tmp/$PNGfile root@${IP}:/tmp
		if [ "$display_reset" == "True"  ]; then
			ssh root@${IP} "cd /tmp; /usr/sbin/eips -c"
			ssh root@${IP} "cd /tmp; /usr/sbin/eips -g $PNGfile"
		else
			ssh root@${IP} "cd /tmp; /usr/sbin/eips -g $PNGfile"
		fi
		sleep $s
	done
done

if [ -n "$post_run" ]; then
	eval $post_run
fi
