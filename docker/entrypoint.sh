#!/bin/bash

# Default to SQLite3
: ${DATABASE:=sqlite}
: ${INSTALL_DIR:=/pootle}
: ${CONFIG_DIR:=/config}

. /scripts/configureDB.sh

: "${DOMAIN:="*"}" # set ALLOWED_HOSTS to '*'

CONFIG_FILE="$CONFIG_DIR/pootle.conf"

if [ ! -f $CONFIG_FILE ]; then
    cd $INSTALL_DIR \
    && . bin/activate || exit 3
    echo "Creating initial Pootle configuration..."
    pootle init --config $CONFIG_FILE $DB_INIT_PARAMS || exit 3
    echo "Created initial Pootle configuration. See documentation for help on customising the settings: http://docs.translatehouse.org/projects/pootle/en/stable-2.7.6/server/settings.html"
    # exit virtualenv
    deactivate || exit 3
fi

# configure Redis

# handle upgrade scenario
    # pootle migrate

# populate fresh install database
    # pootle initdb
