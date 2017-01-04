#!/bin/bash

. /scripts/functions.sh

# Default to SQLite3
: ${DATABASE:=sqlite}
: ${INSTALL_DIR:=/pootle}
: ${POOTLE_SETTINGS:=/config/pootle.conf}
: ${FRESH_INSTALL:=True}

if [ ! -f $POOTLE_SETTINGS ]; then
    FRESH_INSTALL=True
    echo "This is a fresh install"
else
    FRESH_INSTALL=False
fi

if [[ "$FRESH_INSTALL" == "True" ]]; then
    . /scripts/configureDB.sh
    : "${DOMAIN:="*"}" # set ALLOWED_HOSTS to '*'

    cd $INSTALL_DIR \
    && . bin/activate || exit 2
    echo "Creating initial Pootle configuration..."
    pootle init --config $POOTLE_SETTINGS $DB_INIT_PARAMS || exit 2
    echo "Created initial Pootle configuration. See documentation for help on customising the settings: http://docs.translatehouse.org/projects/pootle/en/stable-2.7.6/server/settings.html"
    # exit virtualenv
    deactivate || exit 2

    sed -i -e "s/'PASSWORD': '',/'PASSWORD': '$POOTLE_DB_PASSWORD',/g" $POOTLE_SETTINGS || exit 2
    sed -i -e "s/#'\${your_server}',/'$DOMAIN',/g" $POOTLE_SETTINGS || exit 2

    # configure Redis
    . /scripts/configureCACHES.sh
fi

# handle upgrade scenario
    # pootle migrate

# populate fresh install database
    # pootle initdb
