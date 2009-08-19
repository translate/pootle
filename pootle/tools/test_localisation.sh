#!/bin/bash

basedir=../..

if [ $# -ne 1 ]; then
	echo "$0 lang"
	exit 0
fi

lang=$1

cd $basedir
mkdir locale
./manage.py makemessages --settings=pootle/settings.py -v 1 -e ".html" -e ".py" -l pot
podebug --rewrite=xxx locale/pot/LC_MESSAGES/django.po po/pootle/$lang/pootle.po
rm -rf locale
