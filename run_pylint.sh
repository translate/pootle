#!/bin/bash

config=$1
shift
dirs=$*
pylint --rcfile=$config $ignore_options $(find $dirs -name "*.py" ! -name "test_*.py")
