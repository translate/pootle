#!/bin/sh

python manage.py syncdb --noinput && python initdb.py 

