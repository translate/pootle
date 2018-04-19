#!/bin/bash

cd $APP_SCRIPTS_DIR
./prepare-container
cd $APP_SRC_DIR

export HOME=/home/$APP_USERNAME
exec gosu $APP_USERNAME "$@"
