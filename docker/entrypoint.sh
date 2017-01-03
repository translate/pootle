#!/bin/bash

# Default to SQLite3
: ${DATABASE:=sqlite}
: ${INSTALL_DIR:=/pootle}
: ${CONFIG_DIR:=/config}
: ${FRESH_INSTALL:=True}

CONFIG_FILE="$CONFIG_DIR/pootle.conf"

if [ ! -f $CONFIG_FILE ]; then
    FRESH_INSTALL=True
    echo "This is a fresh install"
else
    FRESH_INSTALL=False
fi

if [[ "$FRESH_INSTALL" == "True" ]]; then
    . /scripts/configureDB.sh
    : "${DOMAIN:="*"}" # set ALLOWED_HOSTS to '*'
fi

if [[ "$FRESH_INSTALL" == "True" ]]; then
    cd $INSTALL_DIR \
    && . bin/activate || exit 2
    echo "Creating initial Pootle configuration..."
    pootle init --config $CONFIG_FILE $DB_INIT_PARAMS || exit 2
    echo "Created initial Pootle configuration. See documentation for help on customising the settings: http://docs.translatehouse.org/projects/pootle/en/stable-2.7.6/server/settings.html"
    # exit virtualenv
    deactivate || exit 2
fi

# configure Redis

# handle upgrade scenario
    # pootle migrate

# populate fresh install database
    # pootle initdb
