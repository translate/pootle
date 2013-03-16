#!/bin/bash

script_name=$(basename $0)
if [ $1 = '--help' -o $1 = '-h' ]; then
	echo "Usage: $script_name [test] [file(s)]"
	echo "       $script_name - run pep8 from current directory"
	echo "       $script_name E2 - run all E2* checks"
	echo "       $script_name E221 dir/ - run E221 in directory dir/"
	exit
fi
select=$1
shift
files=$*
if [ "$files" == ""  ]; then
	files="."
fi

pep8 \
--exclude=djblets,registration,assets,profiles \
--select=$select \
--statistics \
$files
