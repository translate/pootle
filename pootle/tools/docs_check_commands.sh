#!/bin/bash

# Checks that all our ./manage.py commands have at last a django-admin
# marker. Really a simple hack to see that they are documented.

BASE_DIR=$(dirname $0)/../..
DOCS_DIR=$BASE_DIR/docs

pootle_commands=$(
for app in pootle_app import_export virtualfolder
do
    $BASE_DIR/manage.py --help | \
    sed -E -n "/^\[$app\]$/,/^\[/ p" | \
    sed "/^\[/d" | \
    sed "s/^[ ]*//g"
done)

django_commands=$(
    $BASE_DIR/manage.py --help | \
    sed -E -n "/^\[.*\]$/,$ p" | \
    sed "/^\[/d" | \
    sed "s/^[ ]*//g" | \
    sort -u
)

for command in $pootle_commands
do
        egrep -rq "^.. django-admin:: $command" $DOCS_DIR
        if [ $? -eq 1 ]; then
            echo "Missing Pootle docs for $command"
        fi
done

for command in $django_commands
do
    if [[ ! $(echo "$pootle_commands" | egrep $command) ]]; then
        egrep -r --exclude-dir=$DOCS_DIR/_build "manage.py $command" $DOCS_DIR
        egrep -r --exclude-dir=$DOCS_DIR/_build "pootle $command" $DOCS_DIR
        egrep -r --exclude-dir=$DOCS_DIR/_build "\`\`$command\`\`" $DOCS_DIR
    fi
done
