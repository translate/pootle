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
