#!/bin/bash

exec="/usr/sbin/PootleServer"
prog="pootle"

[ -e /etc/sysconfig/$prog ] && . /etc/sysconfig/$prog

prefsfile=${PREFSFILE-/etc/pootle/pootle.prefs}
port=${PORT-"8080"}
pidfile=${PIDFILE-/var/run/pootle.pid}
logfile=${LOGFILE-/var/log/pootle/access.log}
errorfile=${ERRORFILE-/var/log/pootle/errors.log}

[ -x $exec ] || exit 5
[ -f $prefsfile ] || exit 6

$exec -B --port=${port} --prefsfile=${prefsfile} --pidfile=${pidfile} --logerrors=traceback >> $logfile 2>> $errorfile
