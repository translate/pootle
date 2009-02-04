#!/bin/sh

python manage.py syncdb --noinput && python manage.py initdb

