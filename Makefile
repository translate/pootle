CWD = $(shell pwd)
SRC_DIR = ${CWD}/pootle
DOCS_DIR = ${CWD}/docs
STATIC_DIR = ${SRC_DIR}/static
ASSETS_DIR = ${SRC_DIR}/assets
JS_DIR = ${STATIC_DIR}/js
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite
FORMATS=--formats=bztar
TEST_ENV_NAME = pootle_test_env

.PHONY: all build clean sprite test pot mo mo-all requirements help docs assets pep8

all: help

build: docs mo assets
	python setup.py sdist ${FORMATS} ${TAIL}

assets:
	cd ${JS_DIR} && \
	npm update && \
	cd ${CWD}
	python manage.py webpack
	mkdir -p ${ASSETS_DIR}
	python manage.py collectstatic --noinput --clear -i node_modules -i *.jsx ${TAIL}
	python manage.py assets build ${TAIL}
	chmod 664 ${ASSETS_DIR}/.webassets-cache/*

docs:
	# Make sure that the submodule with docs theme is pulled and up-to-date.
	git submodule update --init
	# The following creates the HTML docs.
	# NOTE: cd and make must be in the same line.
	cd ${DOCS_DIR}; make SPHINXOPTS="-W -q" html ${TAIL}

docs-review: docs
	python -mwebbrowser file://$(shell pwd)/${DOCS_DIR}/_build/html/index.html

sprite:
	glue --sprite-namespace="" --namespace="" ${SPRITE_DIR} --css=${CSS_DIR} --img=${IMAGES_DIR}

clean:
	rm -rf ${TEST_ENV_NAME}

test: clean assets
	virtualenv ${TEST_ENV_NAME} && \
	source ${TEST_ENV_NAME}/bin/activate && \
	pip install -r requirements/tests.txt && \
	python setup.py test

pot:
	@${SRC_DIR}/tools/createpootlepot

get-translations:
	ssh pootletranslations ". /var/www/sites/pootle/env/bin/activate; python /var/www/sites/pootle/src/manage.py sync_stores --verbosity=3 --project=pootle"
	rsync -az --delete --exclude="LINGUAS" --exclude=".translation_index" --exclude=pootle-terminology.po pootletranslations:/var/www/sites/pootle/translations/pootle/ ${SRC_DIR}/locale

linguas:
	@${SRC_DIR}/tools/make-LINGUAS.sh 80 > ${SRC_DIR}/locale/LINGUAS

mo:
	python setup.py build_mo ${TAIL}

mo-all:
	python setup.py build_mo --all

pep8:
	@./pootle/tools/pep8.sh travis

publish-pypi:
	python setup.py sdist ${FORMATS} upload

help:
	@echo "Help"
	@echo "----"
	@echo
	@echo "  assets - collect and rebuild the static assets"
	@echo "  build - create sdist with required prep"
	@echo "  docs - build Sphinx docs"
	@echo "  docs-review - launch webbrowser to review docs"
	@echo "  sprite - create CSS sprite"
	@echo "  clean - remove any temporal files"
	@echo "  test - run test suite"
	@echo "  pep8 - run pep8 checks"
	@echo "  pot - update the POT translations templates"
	@echo "  get-translations - retrieve Pootle translations from server (requires ssh config for pootletranslations)"
	@echo "  linguas - update the LINGUAS file with languages over 80% complete"
	@echo "  mo - build MO files for languages listed in 'pootle/locale/LINGUAS'"
	@echo "  mo-all - build MO files for all languages (only use for testing)"
	@echo "  requirements - (re)generate pinned and minimum requirements"
	@echo "  publish-pypi - publish on PyPI"

# Perform forced build using -W for the (.PHONY) requirements target
requirements:
	$(MAKE) -W $(REQFILE) requirements-pinned.txt requirements/min-versions.txt

REQS=.reqs
REQFILE=requirements/base.txt

requirements-pinned.txt: requirements-pinned.txt.in $(REQFILE)
	@echo "# Automatically generated: DO NOT EDIT" > $@
	@echo "# Regenerate using 'make requirements'" >> $@
	@echo >> $@
	@cat $< >> $@
	@set -e;							\
	 case `pip --version` in					\
	   "pip 0"*|"pip 1.[012]"*)					\
	     virtualenv --no-site-packages --clear $(REQS);		\
	     source $(REQS)/bin/activate;				\
	     echo starting clean install of requirements from PyPI;	\
	     pip install --use-mirrors -r $(REQFILE);			\
	     : trap removes partial/empty target on failure;		\
	     trap 'if [ "$$?" != 0 ]; then rm -f $@; fi' 0;		\
	     pip freeze | grep -v '^wsgiref==' | sort -f >> $@ ;;		\
	   *)								\
	     : only pip 1.3.1+ processes --download recursively;	\
	     rm -rf $(REQS); mkdir $(REQS);				\
	     echo starting download of requirements from PyPI;		\
	     pip install --download $(REQS) -r $(REQFILE);		\
	     : trap removes partial/empty target on failure;		\
	     trap 'if [ "$$?" != 0 ]; then rm -f $@; fi' 0;		\
	     (cd $(REQS) && ls *.tar* *.whl |					\
	      sed -e 's/-\([0-9]\)/==\1/' -e 's/\.tar.*$$//') >> $@;	\
	 esac;

requirements/min-versions.txt: requirements/*.txt
	@if grep -q '>[0-9]' $^; then				\
	   echo "Use '>=' not '>' for requirements"; exit 1;	\
	 fi
	@echo "creating $@"
	@echo "# Automatically generated: DO NOT EDIT" > $@
	@echo "# Regenerate using 'make requirements'" >> $@
	@echo "# ====================================" >> $@
	@echo "# Minimum Requirements" >> $@
	@echo "# ====================================" >> $@
	@echo "#" >> $@
	@echo "# These are the minimum versions of dependencies that the Pootle developers" >> $@
	@echo "# claim will work with Pootle." >> $@
	@echo "#" >> $@
	@echo "# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" >> $@
	@echo "#" >> $@
	@echo >> $@
	@cat $^ | sed -n '/=/{s/>=/==/;s/,<.*//;p;}' >> $@
