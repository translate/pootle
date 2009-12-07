#!/bin/bash

exec="/usr/sbin/PootleServer"
prog="pootle"

[ -e /etc/sysconfig/$prog ] && . /etc/sysconfig/$prog

port=${PORT-"8080"}
logfile=${LOGFILE-/var/log/pootle/access.log}
errorfile=${ERRORFILE-/var/log/pootle/errors.log}

[ -x $exec ] || exit 5
[ -f $prefsfile ] || exit 6

PYTHONPATH=$PYTHONPATH:/usr/lib/python2.5/site-packages/Pootle $exec --port=${port} >> $logfile 2>> $errorfile
