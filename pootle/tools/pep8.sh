#!/bin/bash

script_name=$(basename $0)
if [ $# -eq 1 ]; then
	if [ $1 = '--help' -o $1 = '-h' ]; then
		echo "Usage: $script_name [test] [file(s)]"
		echo "       $script_name - run pep8 from current directory"
		echo "       $script_name E2 - run all E2* checks"
		echo "       $script_name E221 dir/ - run E221 in directory dir/"
		exit
	fi
fi

select=$1
shift
files=$*
if [ "$files" == ""  ]; then
	files="."
fi

if [ "$select" == "travis" ]; then
	# See http://pep8.readthedocs.org/en/latest/intro.html#error-codes
	select="E10,E11,E121,E122,E123,E124,E125,E126,E127,E128,E131,E222,E227,E228,E231,E241,E251,E261,E262,E27,E302,E303,E401,E502,E70,E711,E712,E713,E721,W191,W291,W292,W293,W391,W60"
fi

# Add patterns for parts to be excluded:
# - migrations - auto generated so lets not PEP8 them
exclude=migrations

# Match styleguide maximum line length:
# http://docs.translatehouse.org/projects/translate-toolkit/en/latest/developers/styleguide.html#maximum-line-length
max_line_length=84

pep8 \
--exclude=$exclude \
--select=$select \
--statistics \
--max-line-length=$max_line_length \
$files
