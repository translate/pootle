CWD = $(shell pwd)
SRC_DIR = ${CWD}/pootle
DOCS_DIR = ${CWD}/docs
STATIC_DIR = ${SRC_DIR}/static
ASSETS_DIR = ${SRC_DIR}/assets
JS_DIR = ${STATIC_DIR}/js
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite
VERSION=$(shell python setup.py --version)
FULLNAME=$(shell python setup.py --fullname)
SFUSERNAME=$(shell egrep -A5 sourceforge ~/.ssh/config | egrep -m1 User | cut -d" " -f2)
FORMATS=--formats=bztar
TEST_ENV_NAME = pootle_test_env

.PHONY: all build clean sprite test pot mo mo-all help docs assets pep8

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

mo:
	python setup.py build_mo ${TAIL}

mo-all:
	python setup.py build_mo --all

pep8:
	@./pootle/tools/pep8.sh travis

publish-pypi:
	python setup.py sdist ${FORMATS} upload

test-publish-pypi:
	 python setup.py sdist ${FORMATS} upload -r https://testpypi.python.org/pypi

#scp -p dist/translate-toolkit-1.10.0.tar.bz2 jsmith@frs.sourceforge.net:/home/frs/project/translate/Translate\ Toolkit/1.10.0/
publish-sourceforge:
	@echo "We don't trust automation that much.  The following is the command you need to run"
	@echo 'scp -p dist/${FULLNAME}.tar.bz2 ${SFUSERNAME}@frs.sourceforge.net:"/home/frs/project/translate/Pootle/${VERSION}/"'
	@echo 'scp -p docs/releases/${VERSION}.rst ${SFUSERNAME}@frs.sourceforge.net:"/home/frs/project/translate/Pootle/${VERSION}/README.rst"'

publish: publish-pypi publish-sourceforge

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
	@echo "  mo - build MO files for languages listed in 'pootle/locale/LINGUAS'"
	@echo "  mo-all - build MO files for all languages (only use for testing)"
	@echo "  publish-pypi - publish on PyPI"
	@echo "  test-publish-pypi - publish on PyPI testing platform"
	@echo "  publish-sourceforge - publish on sourceforge"
	@echo "  publish - publish on PyPI and sourceforge"
