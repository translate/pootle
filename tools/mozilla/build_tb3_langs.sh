#!/bin/bash
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Virtaal.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

##########################################################################
# NOTE: Documentation regarding (the use of) this script can be found at #
# http://translate.sourceforge.net/wiki/toolkit/mozilla_l10n_scripts     #
##########################################################################

BUILD_DIR="/path/to/buid/root"
COMM_DIR="${BUILD_DIR}/comm-central" # Change "../comm-central" on line 35 too if you change this var
#HG_LANGS="af ar as be bg bn-IN ca cs da de el en-GB en-ZA es-AR es-ES et eu fa fi fr fy-NL ga-IE gl gu-IN he hi-IN hu hy-AM id is it ja ja-JP-mac ka kn ko ku langs lt lv mk ml mn mr nb-NO ne-NP nl nn-NO nr nso pa-IN pl ro ru rw si sk sl sq sr ss st sv-SE ta te th tn tr ts uk ve xh zh-CN zh-TW zu"
HG_LANGS="af"
L10N_DIR="${BUILD_DIR}/l10n"
PO_DIR="${BUILD_DIR}/po"
POPACK_DIR="${BUILD_DIR}/popacks"
PORECOVER_DIR="${BUILD_DIR}/po-recover"
POT_INCLUDES="../README.mozilla-pot"
POTPACK_DIR="${BUILD_DIR}/potpacks"
POUPDATED_DIR="${BUILD_DIR}/po-updated"
PRODUCT_DIRS="mail editor other-licenses/branding/thunderbird" # Directories in language repositories to clear before running po2moz
LANGPACK_DIR="${BUILD_DIR}/xpi"
TB_VERSION="3.0b3"


# Include current dir in path (for buildxpi and others)
CURDIR=`dirname $0`
if [ x"${CURDIR}" == x ] || [ x"${CURDIR}" == x. ]; then
	CURDIR=`pwd`
fi
PATH=${CURDIR}:${PATH}

# Make sure all directories exist
for dir in ${COMM_DIR} ${L10N_DIR} ${PO_DIR} ${POPACK_DIR} ${PORECOVER_DIR} ${POTPACK_DIR} ${POUPDATED_DIR} ${LANGPACK_DIR}
do
	[ ! -d ${dir} ] && mkdir -p ${dir}
done

# Compute relative paths of ${L10N_DIR} and ${POUPDATED_DIR}.
# (This assumes that both directories are sub-directories of ${BUILD_DIR}
L10N_DIR_REL=`echo ${L10N_DIR} | sed "s#${BUILD_DIR}/##"`
POUPDATED_DIR_REL=`echo ${POUPDATED_DIR} | sed "s#${BUILD_DIR}/##"`

(cd ${COMM_DIR}; hg pull -u; hg update -C)
(find ${COMM_DIR} -name '*.orig' | xargs rm) || /bin/true

cd ${L10N_DIR}

# Update all Mercurial-managed languages
for lang in ${HG_LANGS}
do
	[ -d ${lang}/.hg ] && (cd ${lang}; hg revert --all -r default; hg pull -u; hg update -C)
	(find ${lang} -name '*.orig' | xargs rm) || /bin/true
done

rm en-US
rm -rf pot

# en-US and all languages should be up-to-date now
[ -d en-US_mail ] && rm -rf en-US_mail
get_moz_enUS.py -s ../comm-central -d . -p mail -v
mv en-US{,_mail}
ln -sf en-US_mail ./en-US
# CREATE POT FILES FROM en-US
moz2po --progress=none -P --duplicates=msgctxt --exclude '.hg' en-US pot
find pot \( -name '*.html.pot' -o -name '*.xhtml.pot' \) -exec rm -f {} \;

# Create POT pack
# Comment out the lines starting with "tar" and/or "zip" to keep from building archives in the specific format(s).
PACKNAME="${POTPACK_DIR}/thunderbird-${TB_VERSION}-`date +%Y%m%d`"
tar chjf ${PACKNAME}.tar.bz2 pot en-US ${POT_INCLUDES}
zip -qr9 ${PACKNAME}.zip pot en-US ${POT_INCLUDES}

# The following functions are used in the loop following it
function copyfile {
	filename=$1
	language=$2
	directory=$(dirname $filename)
	if [ -f ${L10N_DIR}/en-US/$filename ]; then
		mkdir -p ${L10N_DIR}/$language/$directory
		cp -p ${L10N_DIR}/en-US/$filename ${L10N_DIR}/$language/$directory
	fi
}

function copyfiletype {
	filetype=$1
	language=$2
	files=$(cd ${L10N_DIR}/en-US; find . -name "$filetype")
	for file in $files
	do
		copyfile $file $language
	done
}

function copydir {
	dir=$1
	language=$2
	if [ -d ${L10N_DIR}/en-US/$dir ]; then
		files=$(cd ${L10N_DIR}/en-US/$dir; find . -type f)
		for file in $files
		do
			copyfile $dir/$file $language
		done
	fi
}

for lang in ${HG_LANGS}
do
	## RECOVER - Recover PO files from existing l10n directory.
	## Comment out the following "moz2po"-line if recovery should not be done.
	[ ! -d ${PORECOVER_DIR}/${lang} ] && mkdir -p ${PORECOVER_DIR}/${lang}
	#moz2po --progress=none --errorlevel=traceback --duplicates=msgctxt --exclude=".#*" --exclude='.hg' \
	#	-t ${L10N_DIR}/en-US ${L10N_DIR}/${lang} ${PORECOVER_DIR}/${lang}

	[ ! -d ${PO_DIR}/${lang} ] && cp -R ${PORECOVER_DIR}/${lang} ${PO_DIR}

	# Try and update existing PO files
	updated=""
	[ -z ${updated} ] && [ -d ${PO_DIR}/${lang}/CVS ] && (cd ${PO_DIR}/${lang}; cvs up) && updated="1"
	[ -z ${updated} ] && [ -d ${PO_DIR}/${lang}/.hg ] && (cd ${PO_DIR}/${lang}; hg pull -u) && updated="1"
	[ -z ${updated} ] && [ -d ${PO_DIR}/${lang}/.svn ] && (cd ${PO_DIR}/${lang}; svn up) && updated="1"

	# Copy directory structure while preserving version control metadata
	rm -rf ${POUPDATED_DIR}/${lang}
	cp -R ${PO_DIR}/${lang} ${POUPDATED_DIR}
	find ${POUPDATED_DIR}/${lang} -name '*.po' -exec rm -f {} \;

	## MIGRATE - Migrate PO files to new POT files.
	# Comment out the following "pomigrate2"-line if migration should not be done.
	tempdir=`mktemp -d`
	cp -R ${PO_DIR}/${lang} ${tempdir}/${lang}
	pomigrate2 --use-compendium --quiet --pot2po ${tempdir}/${lang} ${POUPDATED_DIR}/${lang} ${L10N_DIR}/pot
	rm -rf ${tempdir}

	# Pre-po2moz hacks
	lang_product_dirs=
	for dir in ${PRODUCT_DIRS}; do lang_product_dirs="${lang_product_dirs} ${L10N_DIR}/$lang/$dir"; done
	[ -d ${L10N_DIR}/${lang} ] && find ${lang_product_dirs} \( -name '*.dtd' -o -name '*.properties' \) -exec rm -f {} \;
	find ${POUPDATED_DIR} \( -name '*.html.po' -o -name '*.xhtml.po' \) -exec rm -f {} \;

	## PO2MOZ - Create Mozilla l10n layout from migrated PO files.
	# Comment out the "po2moz"-line below to prevent l10n files to be updated to the current PO files.
	po2moz --progress=none --errorlevel=traceback --exclude=".svn" --exclude=".hg" \
		-t ${L10N_DIR}/en-US -i ${POUPDATED_DIR}/${lang} -o ${L10N_DIR}/${lang}

	# Copy files not handled by moz2po/po2moz
	copyfiletype "*.xhtml" ${lang} # Our XHTML and HTML is broken
	copyfiletype "*.html" ${lang}
	copyfiletype "*.rdf" ${lang}   # Don't support .rdf files
	copyfiletype "*.txt" ${lang}
	
	## CREATE PO PACK - Create archives of PO files.
	# Comment out the lines starting with "tar" and/or "zip" to keep from building archives in the specific format(s).
	PACKNAME="${POPACK_DIR}/thunderbird-${TB_VERSION}-${lang}-`date +%Y%m%d`"
	(
		cd ${BUILD_DIR}
		tar cjf ${PACKNAME}.tar.bz2 --exclude '.svn' --exclude '.hg' ${L10N_DIR_REL}/${lang} ${POUPDATED_DIR_REL}/${lang}
		zip -qr9 ${PACKNAME}.zip ${L10N_DIR_REL}/${lang} ${POUPDATED_DIR_REL}/${lang} -x '*.svn*' -x "*.hg*"
	)

	## CREATE XPI LANGPACK
	# Comment out the "buildxpi"-line below if XPI langpacks should not be built.
	#buildxpi.py -L ${L10N_DIR} -s ${COMM_DIR} -o ${LANGPACK_DIR} -p mail ${lang}
done
