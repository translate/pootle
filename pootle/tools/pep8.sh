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

if [ "$select" == "travis" ]; then
	# See http://pep8.readthedocs.org/en/latest/intro.html#error-codes
	select="E10,E11,E251,E261,E262,E27,E401,E70,E711,E721,W191,W291,W292,W293,W391,W60"
fi

pep8 \
--exclude=djblets,assets,profiles,migrations \
--select=$select \
--statistics \
$files
