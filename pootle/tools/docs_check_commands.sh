#!/bin/bash

# Checks that all our ./manage.py commands have at last a pootle_command
# marker. Really a simple hack to see that they are documented.

BASE_DIR=$(dirname $0)/../..
DOCS_DIR=$BASE_DIR/docs

commands=$(
for app in pootle_app import_export virtualfolder
do
    $BASE_DIR/manage.py --help | \
    sed -E -n "/^\[$app\]$/,/^\[/ p" | \
    sed "/^\[/d" | \
    sed "s/^[ ]*//g"
done)

for command in $commands
do
        egrep -rq "^.. pootle_command:: $command" $DOCS_DIR
        if [ $? -eq 1 ]; then
            echo "Missing docs for $command"
        fi
done
