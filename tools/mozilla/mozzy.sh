#!/bin/bash -e
# Based heavily on Rail Aliev's translate-toolkit-mozilla script:
# http://bitbucket.org/rail/translate-toolkit-mozilla

for external in buildxpi.py get_moz_enUS.py moz2po pomigrate2 po2moz wget
do
	if [ -z `which $external` ]; then
		echo "Could not find $external in PATH"
		exit 1
	fi
done

CWD=$(pwd)
GECKO_VERSION="1.9.1"
LANGS="xx"
PRODUCT="browser"
#L10N_BASE_URL="http://hg.mozilla.org/l10n-central"
L10N_BASE_URL="http://hg.mozilla.org/releases/l10n-mozilla-$GECKO_VERSION"
L10N_DIR="l10n"
LANGPACK_DIR="xpi"
PHASEDIRS="config1 config2 configx install lang mac never notnb other security unix user1 user2 user3 user4 win"
PO_URL_HG=
PO_URL_HTTP=
PO_URL_SVN=
SOURCE_DIR="mozilla-$GECKO_VERSION"
#SOURCE_URL="http://hg.mozilla.org/mozilla-central"
SOURCE_URL="http://hg.mozilla.org/releases/mozilla-$GECKO_VERSION"
VERBOSE=1

debuglog() {
	[[ x$VERBOSE != x ]] && echo ">>> $*"
}

function usage() {
	echo "Usage `basename $0` [options]"
	echo
	echo "Options:"
	echo "   --fennec                 - Set defaults for Fennec building. Implies:"
	echo "                                  --l10n-dir=l10n-central"
	echo "                                  --l10n-repo-url=http://hg.mozilla.org/l10n-central/"
	echo "                                  --lang-po-url=http://pootle.locamotion.org/archives/fennec/fennec-%LANG%.tar.bz2"
	echo "                                  --moz-product=mobile"
	echo "                                  --src-dir=mobile"
	echo "                                  --src-repo-url=http://hg.mozilla.org/mobile-browser/"
	echo "   --gecko-ver=<version>    - The Gecko version to build. Equivalent to (replace %VER% with given value):"
	echo "                                  --l10n-repo-url=http://hg.mozilla.org/releases/l10n-mozilla-%VER%"
	echo "                                  --src-dir=mozilla-%VER%"
	echo "                                  --src-repo-url=http://hg.mozilla.org/releases/mozilla-%VER%"
	echo "   --l10n-dir=<dir>         - The directory where Mozilla l10n files live (default: $L10N_DIR)"
	echo "   --l10n-repo-url=<url>    - The base URL (without language code) of Mozilla l10n repositories (default: $L10N_BASE_URL)"
	echo "   --lang-po-hg=<url>       - The Mercurial repository URL where language PO files should be checked out from"
	echo "                              (%LANG% is replaced with the language code)"
	echo "   --lang-po-http=<url>     - The URL where a tarball of language PO files should be downloaded from"
	echo "                              (%LANG% is replaced with the language code)"
	echo "   --lang-po-svn=<url>      - The Subversion repository URL where language PO files should be checked out from"
	echo "                              (%LANG% is replaced with the language code)"
	echo "   --langs=aa[,bb[,cc]]     - Handle specified languages (default: $LANGS)"
	echo "   --moz-product=<prod>     - The Mozilla product name (default: $PRODUCT)"
	echo "   --skip-en                - Don't extract en-US from the Mozilla source tree"
	echo "   --skip-lang-get-po       - Don't get language PO files from Pootle server"
	echo "   --skip-lang-mozgen       - Don't generate Mozilla l10n files from updated PO files"
	echo "   --skip-lang-pull         - Don't pull Mozilla l10n files from Mozilla repositories"
	echo "   --skip-lang-update       - Don't update the language's PO files from its VCS"
	echo "   --skip-lang-update-po    - Don't update PO files to current POT files"
	echo "   --skip-lang-xpi          - Don't build language packs"
	echo "   --skip-langs             - Skip processing of individual languages"
	echo "   --skip-pot               - Don't create POT files (it should already exist)"
	echo "   --skip-src-pull          - Don't do \"hg pull\" in Mozilla source repository directory"
	echo "   --src-dir=<dir>          - The directory containing the Mozilla source repository (default: $SOURCE_DIR)"
	echo "   --src-repo-url=<url>     - The URL of the Mozilla source repository (default: $SOURCE_URL)"
	echo "   --xpi-dir=<dir>          - The output directory for language packs (default: $LANGPACK_DIR)"
	exit 1
}

SKIP_EN=
SKIP_LANG_GETPO=
SKIP_LANG_MOZGEN=
SKIP_LANG_PULL=
SKIP_LANG_UPDATE=
SKIP_LANG_UPDATE_PO=
SKIP_LANG_XPI=
SKIP_LANGS=
SKIP_POT=
SKIP_SRC_PULL=

##### COMMAND-LINE ARGUMENT PROCESSING #####
while true
do
	case $1 in
		--fennec)
			L10N_DIR="l10n-central"
			L10N_BASE_URL="http://hg.mozilla.org/l10n-central/"
			PO_URL_HTTP="http://pootle.locamotion.org/archives/fennec/fennec-%LANG%.tar.bz2"
			PRODUCT="mobile"
			SOURCE_DIR="mobile"
			SOURCE_URL="http://hg.mozilla.org/mobile-browser/"
			shift
			;;
		--gecko-ver=*)
			GECKO_VERSION=$(echo $1 | sed 's/\-\-gecko\-ver=//')
			L10N_BASE_URL="http://hg.mozilla.org/releases/l10n-mozilla-$GECKO_VERSION"
			SOURCE_DIR="mozilla-$GECKO_VERSION"
			SOURCE_URL="http://hg.mozilla.org/releases/mozilla-$GECKO_VERSION"
			shift
			;;
		--l10n-dir=*)
			L10N_DIR=$(echo $1 | sed 's/\-\-l10n\-dir=//')
			shift
			;;
		--l10n-repo-url=*)
			L10N_BASE_URL=$(echo $1 | sed 's/\-\-l10n\-repo\-url=//')
			shift
			;;
		--lang-po-hg=*)
			PO_URL_HG=$(echo $1 | sed 's/\-\-lang\-po\-hg=//')
			shift
			;;
		--lang-po-http=*)
			PO_URL_HTTP=$(echo $1 | sed 's/\-\-lang\-po\-http=//')
			shift
			;;
		--lang-po-svn=*)
			PO_URL_SVN=$(echo $1 | sed 's/\-\-lang\-po\-svn=//')
			shift
			;;
		--langs=*)
			LANGS=$(echo $1 | sed 's/\-\-langs=//; s/,/ /g')
			shift
			;;
		--moz-product=*)
			PRODUCT=$(echo $1 | sed 's/\-\-moz\-product=//')
			shift
			;;
		--skip-en)
			# Don't extract en-US from the source tree
			SKIP_EN=1
			shift
			;;
		--skip-lang-get-po)
			# Don't get language PO files from the Pootle server
			SKIP_LANG_GETPO=1
			shift
			;;
		--skip-lang-mozgen)
			# Don't generate Mozilla l10n files from updated PO files
			SKIP_LANG_MOZGEN=1
			shift
			;;
		--skip-lang-pull)
			# Don't pull Mozilla l10n files from Mozilla repository
			SKIP_LANG_PULL=1
			shift
			;;
		--skip-lang-update)
			# Don't update the language's PO files from its VCS
			SKIP_LANG_UPDATE=1
			shift
			;;
		--skip-lang-update-po)
			# Don't update PO files to current POT files
			SKIP_LANG_UPDATE_PO=1
			shift
			;;
		--skip-lang-xpi)
			# Don't build language packs
			SKIP_LANG_XPI=1
			shift
			;;
		--skip-langs)
			# Skip processing of individual languages
			SKIP_LANGS=1
			shift
			;;
		--skip-pot)
			# Don't create POT files (it should already exist)
			SKIP_POT=1
			shift
			;;
		--skip-src-pull)
			# Don't do "hg pull" in Mozilla source repo dir
			SKIP_SRC_PULL=1
			shift
			;;
		--src-dir=*)
			SOURCE_DIR=$(echo $1 | sed 's/\-\-src\-dir=//')
			shift
			;;
		--src-repo-url=*)
			SOURCE_URL=$(echo $1 | sed 's/\-\-src\-repo\-url=//')
			shift
			;;
		--xpi-dir=*)
			LANGPACK_DIR=$(echo $1 | sed 's/\-\-xpi\-dir=//')
			shift
			;;
		-*|--*)
			usage
			;;
		*)
			break
			;;
	esac
done
############################################

for dir in $L10N_DIR $LANGPACK_DIR po po-updated
do
	if [ ! -d $dir ]; then
		debuglog "Creating directory: $dir"
		mkdir -p $dir
		[ ! -d $dir ] && echo "Unable to create directory: $dir" && exit 2
	fi
done

##### FUNCTIONS #####
update_hg() {
	url=$1
	dir=$2
	hgfailed=
	if [ -d $dir -a -d $dir/.hg ]; then
		debuglog "Updating repository: $dir"
		pushd $dir > /dev/null
		hg revert --all -r default --no-backup
		hg pull -u
		hg update -C
		popd > /dev/null
	else
		[ -d $dir ] && rm -rf $dir
		debuglog "Cloning repository $url to $dir"
		mkdir -p $dir
		rmdir $dir
		hg clone $url $dir || hgfailed=1
	fi

	true
}

get_po_files() {
	lang=$1
	if [[ x$PO_URL_HG == x && x$PO_URL_HTTP == x && x$PO_URL_SVN == x ]]; then
		return
	fi

	if [ -d po/$lang ]; then
		debuglog "Language directory exists: po/$lang. Moving to po/$lang.$$."
		if [ -d po/$lang.$$ ]; then
			debuglog "Backup language directory exists: po/$lang.$$. Deleting it."
			rm -rm po/$lang.$$
		fi
		mv po/${lang} po/$lang.$$
	fi

	if [[ x$PO_URL_HTTP != x ]]; then
		wget_url=$(echo $PO_URL_HTTP | sed "s/%LANG%/$lang/g")
		debuglog "Getting PO files from HTTP server: $wget_url"
		wget $wget_url -O po/$lang.tar.bz2
		if [ $? != 0 ]; then
			echo "Failed to get PO files for language $lang from $wget_url"
			return
		fi

		pushd po > /dev/null
		tar xf $lang.tar.bz2

		# Check if the PO files are split up into phases
		phased=1
		for phase in $PHASEDIRS; do
			if [ ! -d $lang/$phase ]; then
				phased=
				break
			fi
		done

		# If it is split up into phases, copy all files to $lang/
		if [ -n $phased ]; then
			for phase in $PHASEDIRS; do
				cp -R $lang/$phase/* $lang
				rm -rf $lang/$phase
			done
		fi

		popd > /dev/null
	elif [[ x$PO_URL_SVN != x ]]; then
		svn_url=$(echo $PO_URL_SVN | sed "s/%LANG%/$lang/g")
		debuglog "Checking out PO files from Subversion repository: $svn_url"
		(cd po; svn checkout $svn_url $lang)
	elif [[ x$PO_URL_HG != x ]]; then
		hg_url=$(echo $PO_URL_HG | sed "s/%LANG%/$lang/g")
		debuglog "Cloning PO files from Mercurial repository: $hg_url"
		(cd po; hg clone $hg_url $lang)
	fi
}

update_po() {
	lang=$1
	debuglog "<update_po lang=$lang>"
	po_dir=po/$lang
	po_updated_dir=po-updated/$lang

	# Update from VCS
	[ -d $po_dir/.hg ]  && (cd $po_dir && hg revert --all -r default --no-backup && hg pull -u && hg update -C)
	[ -d $po_dir/.svn ] && (cd $po_dir && svn up)

	rm -rf $po_updated_dir
	# Preserve VCS metadata
	cp -R $po_dir $po_updated_dir
	find $po_updated_dir -name '*.po' -exec rm -f '{}' \;

	if [[ x$SKIP_LANG_UPDATE_PO == x ]]; then
		tempdir=`mktemp -d`
		cp -R $po_dir $tempdir
		pomigrate2 --use-compendium --quiet --pot2po $tempdir $po_updated_dir pot
		rm -rf $tempdir
	fi
	debuglog "</update_po lang=$lang>"
}

merge_back() {
	lang=$1
	debuglog "<merge_back lang=$lang>"
	if [ -d po-updated/$lang ]; then
		po2moz --progress=none --errorlevel=traceback --exclude=".svn" --exclude=".hg*" \
			-t en-US -i po-updated/$lang -o $L10N_DIR/$lang
	else
		echo "Could not file updated PO directory: $(pwd)/po-updated/$lang"
	fi
	debuglog "</merge_back lang=$lang>"
}

build_xpi() {
	lang=$1
	debuglog "<buildxpi lang=$lang>"
	if [ -d $L10N_DIR/$lang ]; then
		buildxpi.py -d -L $L10N_DIR -s $SOURCE_DIR -o $LANGPACK_DIR $lang || true
	else
		echo "Could not find l10n directory: $L10N_DIR/$lang"
	fi
	debuglog "</buildxpi lang=$lang>"
}
#####################


##### MAIN START #####
if [[ x$SKIP_SRC_PULL == x ]]; then
	# Update source repository
	update_hg $SOURCE_URL $SOURCE_DIR
fi

enUSchanged=
if [[ x$SKIP_EN == x ]]; then
	# Get en-US files
	[ -d en-US.old ] && rm -rf en-US.old
	[ -d en-US ] && mv en-US{,.old} || enUSchanged=1

	debuglog "Extracting en-US for product \"$PRODUCT\" from $SOURCE_DIR"
	srcdir=$SOURCE_DIR
	#[ $PRODUCT = 'fennec' ] && srcdir=""
	get_moz_enUS.py -s $srcdir -d . -p "$PRODUCT" -v

	if [ -d en-US.old ]; then
		diff en-US{,.old} > /dev/null
		[ $? != 0 ] && echo "en-US changed" && enUSchanged=1
		rm -rf en-US.old
	fi
fi

if [[ x$SKIP_POT == x ]]; then
	# Generate POT files
	if [[ x$enUSchanged != x ]]; then
		if [ -d pot ]; then
			rm -rf pot
		fi
		debuglog "Generating POT files from en-US"
		moz2po --progress=none -P --duplicates=msgctxt en-US pot
	else
		debuglog "No changes in en-US. POT generation skipped."
	fi
fi

[[ x$SKIP_LANGS == x ]] || exit 0

# Update language l10n files
for l in $LANGS; do
	debuglog "<language name=$l>"
	[[ x$SKIP_LANG_PULL == x ]] && update_hg $L10N_BASE_URL/$l $L10N_DIR/$l
	[ ! -d "$L10N_DIR/$l" ] && cp -R en-US "$L10N_DIR/$l"
	#FIXME: The following should be done by moz2po, ie. moz2po should copy files from
	#       the en-US that is not present in the translation.
	[ ! -d "$L10N_DIR/$l" ] && mkdir -p $L10N_DIR/$l && cp -R en-US/* $L10N_DIR/$l
	[[ x$SKIP_LANG_GETPO == x ]] && get_po_files $l
	[ ! -d po/$l ] && echo "!!! Skipping language $l" && continue
	[[ x$SKIP_LANG_UPDATE == x && x$enUSchanged == x ]] && update_po $l
	[[ x$SKIP_LANG_MOZGEN == x ]] && merge_back $l
	[[ x$SKIP_LANG_XPI == x ]]    && build_xpi $l
	debuglog "</language>"
done
######################
