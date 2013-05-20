SRC_DIR = pootle
DOCS_DIR = docs
STATIC_DIR = ${SRC_DIR}/static
ASSETS_DIR = ${SRC_DIR}/assets
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite
VERSION=$(shell python setup.py --version)
FULLNAME=$(shell python setup.py --fullname)
FORMATS=--formats=bztar

.PHONY: all build sprite pot mo mo-all help docs assets

all: help

build: docs mo assets
	python setup.py sdist ${FORMATS} ${TAIL}

assets:
	mkdir -p ${ASSETS_DIR}
	python manage.py collectstatic --noinput --clear ${TAIL}
	python manage.py assets build ${TAIL}

docs:
	# Make sure that the submodule with docs theme is pulled and up-to-date.
	git submodule update --init
	# The following creates the HTML docs.
	# NOTE: cd and make must be in the same line.
	cd ${DOCS_DIR}; make html ${TAIL}

sprite:
	glue --sprite-namespace="" --namespace="" ${SPRITE_DIR} --css=${CSS_DIR} --img=${IMAGES_DIR}

pot:
	@${SRC_DIR}/tools/createpootlepot

mo:
	python setup.py build_mo ${TAIL}

mo-all:
	python setup.py build_mo --all

publish-pypi:
	python setup.py sdist ${FORMATS} upload

test-publish-pypi:
	 python setup.py sdist ${FORMATS} upload -r https://testpypi.python.org/pypi

#scp -p dist/translate-toolkit-1.10.0.tar.bz2 jsmith@frs.sourceforge.net:/home/frs/project/translate/Translate\ Toolkit/1.10.0/
publish-sourceforge:
	@echo "We don't trust automation that much.  The following is the command you need to run"
	@echo 'scp -p dist/${FULLNAME}.tar.bz2 jsmith@frs.sourceforge.net:"/home/frs/project/translate/Pootle/${VERSION}/"'
	@echo 'scp -p release/RELEASE-NOTES-${VERSION}.rst jsmith@frs.sourceforge.net:"/home/frs/project/translate/Pootle/${VERSION}/README.rst"'

publish: publish-pypi publish-sourceforge

help:
	@echo "Help"
	@echo "----"
	@echo
	@echo "  build - create sdist with required prep"
	@echo "  sprite - create CSS sprite"
	@echo "  pot - update the POT translations templates"
	@echo "  mo - build MO files for languages listed in 'pootle/locale/LINGUAS'"
	@echo "  mo-all - build MO files for all languages (only use for testing)"
	@echo "  publish-pypi - publish on PyPI"
	@echo "  test-publish-pypi - publish on PyPI testing platform"
	@echo "  publish-sourceforge - publish on sourceforge"
	@echo "  publish - publish on PyPI and sourceforge"
