#!/bin/bash

# Checks that all our pootle runner commands have at last a django-admin
# marker. Really a simple hack to see that they are documented.

BASE_DIR=$(dirname $0)/../..
DOCS_DIR=$BASE_DIR/docs
EGREP_EXCLUDE_DIR="--exclude-dir=$DOCS_DIR/_build"

# pootle $command

pootle_commands=$(
for app in pootle_app import_export virtualfolder
do
    pootle | \
    sed -E -n "/^\[$app\]$/,/^\[/ p" | \
    sed "/^\[/d" | \
    sed "s/^[ ]*//g"
done)

django_commands=$(
    pootle | \
    sed -E -n "/^\[.*\]$/,$ p" | \
    sed "/^\[/d" | \
    sed "s/^[ ]*//g" | \
    sort -u
)

echo
echo "Missing '.. django-admin::' markers for the following commands"
for command in $pootle_commands
do
        egrep -rq $EGREP_EXCLUDE_DIR "^.. django-admin:: $command" $DOCS_DIR
        if [ $? -eq 1 ]; then
            echo ".. django-admin:: $command"
        fi
done

echo
echo "No command references ':djadmin:' for the following commands"
for command in $pootle_commands
do
        egrep -rq $EGREP_EXCLUDE_DIR ":djadmin:\`$command\`" $DOCS_DIR
        if [ $? -eq 1 ]; then
            echo ":djadmin:\`$command\`"
        fi
done

echo
echo "Potential missing links to Django management commands need :djadmin:"
for command in $django_commands
do
    if [[ ! $(echo "$pootle_commands" | egrep $command) ]]; then
        egrep -r $EGREP_EXCLUDE_DIR "manage.py $command ?[^<]" $DOCS_DIR
        egrep -r $EGREP_EXCLUDE_DIR  "pootle $command" $DOCS_DIR
        egrep -r $EGREP_EXCLUDE_DIR  "\`\`$command\`\`" $DOCS_DIR
    fi
done

echo
echo "We don't want manage.py \$command we want pootle \$command"
for command in $django_commands
do
    if [[ ! $(echo "$pootle_commands" | egrep $command) ]]; then
        egrep -r $EGREP_EXCLUDE_DIR "manage.py $command ?[^<]" $DOCS_DIR
    fi
done


# POOTLE_* settings

settings=$(egrep -h $EGREP_EXCLUDE_DIR "^POOTLE_" $(ls $BASE_DIR/pootle/settings/*.conf | egrep -v $EGREP_EXCLUDE_DIR "90-.*.conf$") | sed "s/\w*=.*$//g")

echo
echo "Missing '.. setting::' markers for the following settings"
for setting in $settings
do
    egrep -rq $EGREP_EXCLUDE_DIR "^.. setting:: $setting" $DOCS_DIR
    if [ $? -eq 1 ]; then
        echo "..setting:: $setting"
    fi
done

echo
echo "No setting references ':setting:' for the following settings"
for setting in $settings
do
    egrep -rq $EGREP_EXCLUDE_DIR ":setting:\`$setting\`" $DOCS_DIR
    if [ $? -eq 1 ]; then
        echo ":setting:\`$setting\`"
    fi
done

IGNORABLE_ALLCAPS_ENTRIES="(HEAD|PYTHONPATH|UTC|POOTLE_TOP_STATS_CACHE_TIMEOUT|ENVIRONMENT|POOTLE_ENABLE_API|DEPRECATIONS)"

echo
echo "ALL_CAPS that could be :envvar: or :setting:"
egrep -rh $EGREP_EXCLUDE_DIR --exclude=$DOCS_DIR/server/settings.rst "\`\`[A-Z][A-Z_]{1,}\`\`" $DOCS_DIR | egrep -v $IGNORABLE_ALLCAPS_ENTRIES
